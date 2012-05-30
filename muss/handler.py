class Mode(object):

    """
    Dummy class to be extended by classes acting as modes.

    In-game interaction is modal: when a client sends a line, the resulting behavior will be different depending on what's going on. The user may be logging in, or sending an ordinary command, or responding to a prompt.

    Mode classes should override the handle() method, which the protocol will call on the active mode when a line is received from the client.
    """

    def handle(self, player, line):
        """
        Respond, in whatever way is appropriate, to a line from the client.

        Subclasses are expected to implement this method; the default implementation raises NotImplementedError.

        Args:
            factory: The instance of server.WorldFactory responsible for maintaining state.
            player: The data.Player that sent the line.
            line: The line that was sent.
        """
        raise NotImplementedError("Current mode did not override handle()")


class NormalMode(Mode):

    """
    Our usual mode of behavior. When nothing else has taken over the input, this is what will handle it.
    """

    def handle(self, player, line):
        """
        This will eventually be a command parser. Today, it is starting to be.
        """
        # for example only, obvs
        from commands import Say, Emote, FooOne, FooTwo
        commands = [Say, Emote, FooOne, FooTwo]

        arguments = None
        perfect_matches = []
        partial_matches = []
        for command in commands:
            for name in command.nospace_name:
                if line.startswith(name):
                    arguments = line.split(name, 1)[1]
                    perfect_matches.append((name, command, arguments))
            for name in command.name:
                if " " in line:
                    (first, arguments) = line.split(None, 1)
                else:
                    (first, arguments) = (line, "")
                if name.startswith(first.lower()):
                    if first.lower() == name:
                        perfect_matches.append((name, command, arguments))
                    else:
                        partial_matches.append((name, command, arguments))
        if len(perfect_matches) == 1:
            (name, command, arguments) = perfect_matches[0]
            args = command.args.parseString(arguments).asDict()
            command().execute(player, args)
        elif len(perfect_matches):
            name_matches = [i[0] for i in perfect_matches]
            player.send("I don't know which one you meant: {}?".format(", ".join(name_matches)))
        elif len(partial_matches) == 1:
            (name, command, arguments) = partial_matches[0]
            args = command.args.parseString(arguments).asDict()
            command().execute(player, args)
        elif len(partial_matches):
            name_matches = [i[0] for i in partial_matches]
            player.send("I don't know which one you meant: {}?".format(", ".join(name_matches)))
        else:
            player.send("I don't understand that.")

class Command(object):

    """
    The superclass for all commands -- local or global, built-in or user-defined.
    """
    nospace_name = []
