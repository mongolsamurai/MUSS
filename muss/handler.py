import inspect
import pkgutil
import pyparsing

from twisted.internet import defer

from muss import commands, db, locks, utils, parser


class Mode(object):

    """
    Dummy class to be extended by classes acting as modes.

    In-game interaction is modal: when a client sends a line, the resulting
    behavior will be different depending on what's going on. The user may be
    logging in, or sending an ordinary command, or responding to a prompt.

    Mode classes should override the handle() method, which the protocol will
    call on the active mode when a line is received from the client.

    Attrs:
        blank_line: By default, a blank line follows the output from each line
            from the player. Subclasses may override this to False to suppress
            the blank line.
    """

    blank_line = True

    def handle(self, player, line):
        """
        Respond, in whatever way is appropriate, to a line from the client.

        Subclasses are expected to implement this method; the default
        implementation raises NotImplementedError.

        Args:
            factory: The instance of server.WorldFactory responsible for
                maintaining state.
            player: The db.Player that sent the line.
            line: The line that was sent.
        """
        raise NotImplementedError("Current mode did not override handle()")


class NormalMode(Mode):

    """
    Our usual mode of behavior. When nothing else has taken over the input,
    this is what will handle it.
    """

    def handle(self, player, line):
        """
        Parse the input line for a command and arguments, reporting any errors
        or unresolvable ambiguity.
        """

        line = line.strip()
        if not line:
            return

        split_line = line.split(None, 1)
        if len(split_line) == 1:
            split_line.append("")
        first, rest_of_line = split_line

        name = ""
        command = None

        # Check for nospace commands
        nospace_matches = []
        for command in all_commands():
            for name in command().nospace_names:
                # We can't use find_by_name because we don't know where the
                # nospace command ends.
                if line.startswith(name):
                    # No partial matching, for the same reason.
                    nospace_matches.append((name, command))
        if len(nospace_matches) == 1:
            name, command = nospace_matches[0]
            if len(line) > len(name):
                arguments = line[len(name):]
            else:
                arguments = ""

        try:
            try:
                if len(nospace_matches) > 1:
                    raise parser.AmbiguityError(line, 0, parser.Command.errmsg,
                                                parser.Command, nospace_matches)

                # Check for normal command matches
                pattern = parser.CommandName(fullOnly=True)("command")
                parse_result = pattern.parseString(first, parseAll=True)
                matched = parse_result["command"]
                arguments = rest_of_line
                if nospace_matches:
                    # We found a regular command, but already had a nospace
                    # command.
                    raise parser.AmbiguityError(line, 0, parser.Command.errmsg,
                                                parser.Command,
                                                nospace_matches + [matched])
                else:
                    name, command = parse_result["command"]
            except parser.NotFoundError as e:
                # No commands match, what about exits?
                exits = [(exit.name, exit) for exit in
                         db.find_all(lambda x: x.type == 'exit' and
                                               x.location == player.location)]
                try:
                    pattern = parser.OneOf(exits)("exit").setName("exit")
                    parse_result = pattern.parseString(first, parseAll=True)
                    # OneOf(exits) parsed, so exactly one exit matches.
                    if not nospace_matches:
                        command = commands.world.Go
                        arguments = first
                except parser.AmbiguityError as f:
                    # Multiple exits match and no full commands do.
                    if not nospace_matches:
                        player.send(f.verbose())
                        return
                    # At this point there can only be one nospace command.
                    # Let it fall all the way through to execution.
                except parser.NotFoundError as _:
                    raise e

        except parser.NotFoundError as e:
            if not nospace_matches:
                message = e.verbose()
                # Check whether a require_full command would have matched
                rf_commands = [c for c in all_commands() if c.require_full]
                # (ignoring perfect matches because we would have already seen
                # them)
                rf_matches = utils.find_by_name(e.pstr, rf_commands,
                                                attributes=["names"])[1]
                if len(rf_matches) == 1:
                    rf_name, rf_command = rf_matches[0]
                    message += (" (If you mean \"{},\" you'll need to use the "
                                "whole command name.)".format(rf_name))
                elif rf_matches:
                    rf_names = [c[0] for c in rf_matches]
                    message += (" (If you meant one of these, you'll need to "
                                "use the whole command name: {}.)"
                                .format(", ".join(rf_names)))
                player.send(message)
                return

        except parser.AmbiguityError as e:
            # it's not clear from the name which command the user intended,
            # so see if any of their argument specs match what we got
            parsable_matches = []
            for possible_name, possible_command in e.matches + nospace_matches:
                try:
                    if nospace_matches and ((possible_name, possible_command) ==
                                            nospace_matches[0]):
                        test_arguments = line.split(possible_name, 1)[1]
                    else:
                        test_arguments = rest_of_line
                    pattern = possible_command.args(player)
                    args = pattern.parseString(test_arguments, parseAll=True)
                    parsable_matches.append((possible_name, possible_command))
                except pyparsing.ParseException:
                    # user probably didn't intend this command; skip it.
                    pass
                except utils.UserError:
                    parsable_matches.append((possible_name, possible_command))
            if len(parsable_matches) == 1:
                name, command = parsable_matches[0]
                if len(line) > len(name):
                    if parsable_matches[0] in nospace_matches:
                        arguments = line[len(name):]
                    else:
                        arguments = rest_of_line
                else:
                    arguments = ""
            else:
                if parsable_matches:
                    # we can at least narrow the field a little
                    e.matches = parsable_matches
                player.send(e.verbose())
                return

        # okay! we have a command! let's parse it.
        try:
            args = command.args(player).parseString(arguments, parseAll=True)
            command().execute(player, args)
        except utils.UserError as e:
            if hasattr(e, "verbose"):
                player.send(e.verbose())
            else:
                player.send(str(e))
        except pyparsing.ParseException as e:
            usages = command().usages
            if len(usages) > 1:
                from commands.help import Usage
                player.send("Usage:")
                Usage().execute(player, {"command": (name, command)}, tabs=True)
            else:
                player.send("Usage: " + usages[0])
            player.send("(Try \"help {}\" for more help.)".format(name))


def prompt(player, prompt):
    """
    Sends the given prompt string to the player and returns a Deferred, which
    will be called back with the player's response.
    """
    player.send(prompt)
    mode = LineCaptureMode()
    player.enter_mode(mode)
    return mode.d


class LineCaptureMode(Mode):
    """
    Records one line received, then exits itself and calls back the Deferred.

    If you're trying to prompt the player for input, consider instead the
    prompt function in this module, which uses this Mode.
    """
    blank_line = False  # Override from Mode

    def __init__(self):
        self.d = defer.Deferred()

    def handle(self, player, line):
        player.exit_mode()
        self.d.callback(line)


def all_command_modules():
    """
    Returns a generator yielding every module defined in muss.commands.
    """

    for module_loader, name, ispkg in pkgutil.walk_packages(
            commands.__path__, prefix="muss.commands."):
        # __import__("A.B") returns A unless fromlist is nonempty, in which
        # case it returns A.B -- but we actually want the module, not to import
        # anything from it, hence the [""].
        yield __import__(name, fromlist=[""])


def all_commands():
    """
    Returns a generator yielding every command class defined in every module in
    muss.commands.
    """

    for module in all_command_modules():
        for name in dir(module):
            cls = getattr(module, name)
            if (inspect.isclass(cls) and issubclass(cls, parser.Command) and
                    cls is not parser.Command):
                yield cls
