# Basic interactions in the world.

import pyparsing as pyp
import importlib
from muss import db, parser, equipment, utils


class Equip(parser.Command):
    name = ["equip", "wear", "don"]
    usage = ["equip", "equip <item>", "wear <item>", "don <item>"]
    help_text = ("Equip an item that you are carrying. Without an argument, "
                 "displays the items you're currently wearing.")

    @classmethod
    def args(cls, player):
        return parser.ObjectIn(player)("item") | parser.EmptyLine()

    def execute(self, player, args):
        item = args.get("item")
        if item:
            try:
                item.equip()
            except AttributeError:
                raise utils.UserError("That is not equipment!")
            item.run_event("equip", player)
            player.send("You equip {}.".format(item.name))
            player.emit("{} equips {}.".format(player.name, item.name),
                        exceptions=[player])
        else:
            equipment = player.equipment_string()
            if equipment:
                player.send(equipment)
            else:
                player.send("You have nothing equipped.")


class Unequip(parser.Command):
    name = ["unequip", "remove", "doff"]
    usage = ["unequip <item>", "remove <item>", "doff <item>"]
    help_text = "Remove an item you have equipped."

    @classmethod
    def args(cls, player):
        return parser.ObjectIn(player)("item")

    def execute(self, player, args):
        item = args["item"]
        try:
            item.unequip()
        except AttributeError:
            raise utils.UserError("That is not equipment!")
        item.run_event("unequip", player)
        player.send("You unequip {}.".format(item.name))
        player.emit("{} unequips {}.".format(player.name, item.name),
                    exceptions=[player])


class Give(parser.Command):
    name = ["give", "put"]
    usage = ["give <item> to <player>", "give <player> <item>",
             "put <item> in <object>"]
    help_text = "Give an item to someone, or put one object in another."

    @classmethod
    def args(cls, player):
        item = parser.ObjectIn(player)
        destination = parser.NearbyObject(player)
        return (item("item") + pyp.Keyword("to") + destination("destination")
               | destination("destination") + item("item")
               | item("item") + pyp.Keyword("in") + destination("destination"))

    def execute(self, player, args):
        item = args["item"]
        destination = args["destination"]

        if destination is player:
            raise utils.UserError("You already have {}.".format(item))

        item.run_event("give", player, destination=destination)

        item.location = destination

        if destination.type == "player":
            player.send("You give {} to {}.".format(item, destination))
            destination.send("{} gives you {}.".format(player, item))
            player.emit("{} gives {} to {}.".format(player, item, destination),
                        exceptions = [player, destination])
        else:
            player.send("You put {} in {}.".format(item, destination))
            player.emit("{} puts {} in {}.".format(player, item, destination),
                        exceptions = [player])


class Drop(parser.Command):
    name = "drop"
    usage = ["drop <item>"]
    help_text = "Drop an item from your inventory into your location."

    @classmethod
    def args(cls, player):
        return parser.ObjectsIn(player)("items")

    def execute(self, player, args):
        item_list = args[0]
        # Why does this work and args["items"] doesn't?
        # I don't know, but it does. I blame pyparsing.
        equipped = [x for x in item_list if hasattr(x, "equipped")
                                            and x.equipped]
        unequipped = [x for x in item_list if x not in equipped]
        if len(unequipped) == 1:
            item = unequipped[0]
        elif not unequipped and len(equipped) == 1:
            item = equipped[0]
        elif unequipped:
            raise parser.AmbiguityError("", 0, "", None,
                                        [(x.name, x) for x in unequipped])
        elif equipped:
            raise parser.AmbiguityError("", 0, "", None,
                                        [(x.name, x) for x in equipped])
        else:
            raise parser.NotFoundError("", 0, "", None)

        was_equipped = hasattr(item, "equipped") and x.equipped
        item.run_event("drop", player)
        item.location = player.location
        if was_equipped:
            player.send("You unequip and drop {}.".format(item.name))
            player.emit("{} unequips and drops {}.".format(player.name,
                        item.name), exceptions=[player])
        else:
            player.send("You drop {}.".format(item.name))
            player.emit("{} drops {}.".format(player.name, item.name),
                        exceptions=[player])


class Go(parser.Command):
    name = "go"
    usage = ["<exit name>", "go <exit name>", "go <uid>"]
    help_text = "Travel through an exit."

    @classmethod
    def args(cls, player):
        return parser.ReachableOrUid(player)("exit")

    def execute(self, player, args):
        try:
            exit = args["exit"]
            exit.run_event("go", player)
            exit.go(player)
        except AttributeError:
            # it has no go() so it isn't an exit
            player.send("You can't go through {}.".format(args["exit"]))


class Inventory(parser.Command):
    name = "inventory"
    help_text = "Shows you what you're carrying."

    def execute(self, player, args):
        inventory = player.contents_string()
        if inventory:
            player.send(inventory)
        else:
            player.send("You are not carrying anything.")


class Look(parser.Command):
    name = ["look", "l"]
    usage = ["look", "look <object>"]
    help_text = ("Show an object's description. If it has contents or exits, "
                 "list them. If it's an exit, show its destination.\n"
                 "You can specify an object either by naming something near "
                 "you or giving its UID. If no object is specified, you will "
                 "look at your current location.")

    @classmethod
    def args(cls, player):
        return parser.ReachableOrUid(player)("obj") | parser.EmptyLine()

    def execute(self, player, args):
        try:
            obj = args["obj"]
            obj.run_event("look", player)
        except KeyError:
            # If invoked without argument, look at our surroundings instead
            obj = player.location

        try:
            player.send(obj.position_string())
        except AttributeError:
            player.send(obj.name)

        try:
            player.send(str(obj.description))
        except AttributeError:
            # A default description is set in Object.__init__, but if you go out
            # of your way to delete it, I guess we won't send anything.
            pass

        population = obj.population_string()
        if population:
            player.send(population)

        contents = obj.contents_string()
        if contents:
            player.send(contents)

        equipment = obj.equipment_string()
        if equipment:
            player.send(equipment)

        exits = obj.exits_string()
        if exits:
            player.send(exits)

        if obj.type == 'exit':
            player.send("Destination: {}".format(obj.destination))


class Take(parser.Command):
    name = ["take", "get"]
    usage = ["take <item>", "get <item>"]
    help_text = "Pick up an item in your location."

    @classmethod
    def args(cls, player):
        return parser.ReachableObject(player, priority="room")("item")

    def execute(self, player, args):
        item = args["item"]
        origin = item.location

        if origin is player:
            raise utils.UserError("You already have {}.".format(item))


        try:
            item.location = player
            item.run_event("get", player)
        except equipment.EquipmentError:
            raise equipment.EquipmentError("You can't, it's equipped.")

        if origin is not player.location:
            player.send("You take {} from {}.".format(item.name, origin))
            origin.send("{} takes {} from you.".format(player, item.name))
            player.emit("{} takes {} from {}." .format(player, item.name,
                                                       origin),
                        exceptions=[player, origin])
        else:
            player.send("You take {}.".format(item.name))
            player.emit("{} takes {}.".format(player.name, item.name),
                        exceptions=[player])
