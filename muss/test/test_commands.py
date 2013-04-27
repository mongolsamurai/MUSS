import mock
import pyparsing as pyp
from twisted.trial import unittest

from muss import db, handler, locks, parser, utils


class CommandTestCase(unittest.TestCase):

    def setUp(self):
        self.patch(locks, "_authority", locks.SYSTEM)
        lobby = db.Room("lobby")
        lobby.uid = 0
        self.patch(db, "_objects", {0: lobby})

        self.player = db.Player("Player", "password")
        self.player.send = mock.MagicMock()
        self.player.location = db._objects[0]
        self.player.enter_mode(handler.NormalMode())
        db.store(self.player)

        self.neighbor = db.Player("PlayersNeighbor", "password")
        self.neighbor.send = mock.MagicMock()
        self.neighbor.location = db._objects[0]
        self.neighbor.enter_mode(handler.NormalMode())
        db.store(self.neighbor)

        self.objects = {}
        for room_object in ["frog", "ant", "horse", "Fodor's Guide", "abacus",
                            "balloon"]:
            self.objects[room_object] = db.Object(room_object,
                                                  self.player.location)
        with locks.authority_of(self.player):
            for inv_object in ["apple", "horse figurine", "ape plushie",
                               "Anabot doll", "cherry", "cheese"]:
                self.objects[inv_object] = db.Object(inv_object, self.player)
        self.objects["room_cat"] = db.Object("cat", self.player.location)
        self.objects["inv_cat"] = db.Object("cat", self.player)
        self.objects["neighbor_apple"] = db.Object("apple", self.neighbor)
        self.objects["hat"] = db.Object("hat", self.objects["frog"])
        for key in self.objects:
            db.store(self.objects[key])

    def assert_command(self, command, test_response=None, startswith=None,
                       endswith=None, contains=None):
        """
        Test that a command sends the appropriate response to the player and,
        optionally, to a neighbor.
        """
        if not (test_response or startswith or endswith or contains):
            raise ValueError("No assertion type specified.")

        with locks.authority_of(self.player):
            self.player.mode.handle(self.player, command)
        response = self.player.send.call_args[0][0]

        if test_response:
            self.assertEqual(response, test_response)
        if startswith:
            # This instead of using .startswith because it produces more useful
            # errors
            self.assertEqual(response[:len(startswith)], startswith)
        if endswith:
            # See previous comment
            self.assertEqual(response[-len(endswith):], endswith)
        if contains:
            self.assertTrue(contains in response)

    def test_usage(self):
        self.assert_command("usage poke", "poke <player>")
        self.assert_command("usage usage", "usage <command>")
        self.assert_command("usage quit", "quit")
        self.assert_command("usage ;", ";<action>")

    def test_inventory(self):
        inv = [i for i in self.objects.values() if i.location == self.player]
        inv_names = sorted([i.name for i in inv])
        inv_string = ", ".join(inv_names)
        self.assert_command("inventory",
                            "You are carrying: {}.".format(inv_string))
        for item in inv:
            db.delete(item)
        self.assert_command("inventory", "You are not carrying anything.")

    def test_take_success(self):
        from muss.commands.world import Take
        args = Take.args(self.player).parseString("balloon")
        Take().execute(self.player, args)
        self.assertEqual(self.objects["balloon"].location, self.player)
        args = Take.args(self.player).parseString("cat")
        Take().execute(self.player, args)
        self.assertEqual(self.objects["room_cat"].location, self.player)
        self.assert_command("take frog", "You take frog.")
        self.assertEqual(self.neighbor.send.call_args[0][0],
                         "Player takes frog.")

    def test_take_failure(self):
        from muss.commands.world import Take
        self.assertRaises(parser.NotFoundError,
                          Take.args(self.player).parseString, "apple")
        self.assertRaises(parser.AmbiguityError,
                          Take.args(self.player).parseString, "f")

    def test_drop_success(self):
        self.assert_command("drop apple", "You drop apple.")
        self.assertEqual(self.neighbor.send.call_args[0][0],
                         "Player drops apple.")
        self.assertEqual(self.objects["apple"].location, self.player.location)

    def test_drop_failure(self):
        from muss.commands.world import Drop
        self.assertRaises(parser.NotFoundError,
                          Drop.args(self.player).parseString, "frog")
        self.assertRaises(parser.AmbiguityError,
                          Drop.args(self.player).parseString, "ch")

    def test_create_success(self):
        self.assert_command("create a widget", startswith="Created item #",
                            endswith=", a widget.")
        self.assert_command("inventory", contains="a widget")

    def test_create_failure(self):
        from muss.commands.building import Create
        self.assert_command("create", "(Try \"help create\" for more help.)")

    def test_open(self):
        with locks.authority_of(self.player):
            destination = db.Room("destination")
            db.store(destination)

        from muss.commands.building import Open
        self.assert_command("open north to #{}".format(destination.uid),
                            "Opened north to destination.")
        exit = db.find(lambda x: x.uid == destination.uid + 1)
        self.assertTrue(isinstance(exit, db.Exit))
        self.assertIdentical(exit.location, self.player.location)
        self.assertIdentical(exit.destination, destination)

    def test_destroy(self):
        with locks.authority_of(self.player):
            apple_uid = self.objects["apple"].uid
            command = "destroy #{}".format(apple_uid)
            response = "You destroy #{} (apple).".format(apple_uid)
            self.assert_command(command, response)
            self.assertEqual(self.neighbor.send.call_args[0][0],
                             "Player destroys apple.")
            matches = db.find_all(lambda x: x.uid == apple_uid)
            self.assertEqual(len(matches), 0)
            self.assertRaises(KeyError, db.get, apple_uid)

            with locks.authority_of(self.objects["frog"]):
                handler.NormalMode().handle(self.objects["frog"], "drop hat")
            with locks.authority_of(self.player):
                handler.NormalMode().handle(self.player, "take hat")
            hat_uid = self.objects["hat"].uid
            self.assert_command("destroy #{}".format(hat_uid),
                                "You cannot destroy hat.")

    def test_ghosts(self):
        self.assert_command("destroy #{}".format(self.player.uid),
                            "You cannot destroy Player.")

    def test_set_string(self):
        from muss.commands.building import Set
        self.assertRaises(AttributeError, getattr, self.player, "test")

        args = Set.args(self.player).parseString("player.test='single quotes'")
        Set().execute(self.player, args)
        self.assertEqual(self.player.test, "single quotes")

        args = Set.args(self.player).parseString(
            "player.test='escaped \\' single'")
        Set().execute(self.player, args)
        self.assertEqual(self.player.test, "escaped ' single")

        args = Set.args(self.player).parseString('player.test="double quotes"')
        Set().execute(self.player, args)
        self.assertEqual(self.player.test, "double quotes")

        args = Set.args(self.player).parseString(
            'player.test="escaped \\" double"')
        Set().execute(self.player, args)
        self.assertEqual(self.player.test, 'escaped " double')

        args = Set.args(self.player).parseString(
            'player.test="""triple \' " quotes"""')
        Set().execute(self.player, args)
        self.assertEqual(self.player.test, 'triple \' " quotes')

    def test_set_numeric(self):
        from muss.commands.building import Set
        self.assertRaises(AttributeError, getattr, self.player, "test")

        args = Set.args(self.player).parseString('player.test=1337')
        Set().execute(self.player, args)
        self.assertEqual(self.player.test, 1337)

    def test_set_uid(self):
        from muss.commands.building import Set
        self.assertRaises(AttributeError, getattr, self.player, "test")

        args = Set.args(self.player).parseString("player.test=#0")
        Set().execute(self.player, args)
        lobby = db.get(0)
        self.assertIs(self.player.test, lobby)

        args = Set.args(self.player).parseString("player.test=#-1")
        self.assertRaises(pyp.ParseException, Set().execute, self.player, args)

        args = Set.args(self.player).parseString("player.test=#99999")
        self.assertRaises(utils.UserError, Set().execute, self.player, args)

    def test_set_keywords(self):
        from muss.commands.building import Set
        self.assertRaises(AttributeError, getattr, self.player, "test")

        args = Set.args(self.player).parseString("player.test=True")
        Set().execute(self.player, args)
        self.assertIs(self.player.test, True)

        args = Set.args(self.player).parseString("player.test=False")
        Set().execute(self.player, args)
        self.assertIs(self.player.test, False)

        args = Set.args(self.player).parseString("player.test=None")
        Set().execute(self.player, args)
        self.assertIs(self.player.test, None)

    def test_set_spaces(self):
        from muss.commands.building import Set
        self.assertRaises(AttributeError, getattr, self.player, "test")

        args = Set.args(self.player).parseString(
            'player . test = "extra spaces"')
        Set().execute(self.player, args)
        self.assertEqual(self.player.test, "extra spaces")

    def test_set_failure(self):
        self.assert_command("set asdf.name='foo'",
                            "I don't know what object you mean by 'asdf'")
        self.assert_command("set player.5='foo'",
                            "'5' is not a valid attribute name.")
        self.assert_command("set player.test=foo",
                            "'foo' is not a valid attribute value.")

    def test_set_name(self):
        self.assert_command("set player.name='Foo'",
                            "You don't have permission to set name on Player.")
        self.assert_command("set apple.name='pear'",
                            "Set apple's name attribute to pear")
        self.assert_command("set cherry.name='#25'",
                            "Names can't begin with a #.")

    def test_unset_success(self):
        with locks.authority_of(self.player):
            self.player.mode.handle(self.player, "set player.test=1")
        self.assert_command("unset player.test",
                            "Unset test attribute on Player.")

    def test_unset_failure(self):
        self.assert_command("unset player.foobar",
                            "Player doesn't have an attribute 'foobar'")
        self.assert_command("unset foobar.name",
                            "I don't know what object you mean by 'foobar'")
        self.assert_command("unset player.name",
                            "You don't have permission to unset name on "
                            "Player.")

    def test_help(self):
        from muss.handler import all_commands

        for command in all_commands():
            names = command().names
            if not names:
                # The only thing this excludes is semipose
                continue
            name = names[0]
            # The command name(s), "Usage:", a blank line, and the help text
            send_count = 4
            send_count += len(command().usages)

            self.player.mode.handle(self.player, "help {}".format(name))
            all_sends = [i[0][0] for i in self.player.send.call_args_list]
            help_sends = all_sends[-send_count:]

            self.assertEqual(help_sends[0][:len(name)], name.upper())
            self.assertEqual(help_sends[1], "Usage:")
            self.assertEqual(help_sends[2:-2],
                             ["\t" + u for u in command().usages])
            self.assertEqual(help_sends[-2], "")
            self.assertEqual(help_sends[-1], command.help_text)

    def test_sudo(self):
        with locks.authority_of(self.neighbor):
            handler.NormalMode().handle(self.neighbor, "create x")
            handler.NormalMode().handle(self.neighbor, "set x.sudotest=5")
            handler.NormalMode().handle(self.neighbor, "drop x")
        self.assert_command("set x.sudotest=6",
                            "You don't have permission to set sudotest on x.")
        self.assert_command("sudo set x.sudotest=6",
                            "Set x's sudotest attribute to 6")

    def test_dig(self):
        self.assert_command("dig", "Enter the room's name:")
        self.assert_command("Room", "Enter the name of the exit into the room, "
                                    "or . for none:")
        self.assert_command("east", "Enter the name of the exit back, or . for "
                                    "none:")
        self.assert_command("west", "Done.")

    def test_dig_oneline(self):
        self.assert_command("dig Another Room", "Enter the name of the exit "
                                                "into the room, or . for none:")
        self.assert_command("west", "Enter the name of the exit back, or . for "
                                    "none:")
        self.assert_command("east", "Done.")
