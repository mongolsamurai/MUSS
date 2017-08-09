import db, locks

class Event(db.Object):
    """
    A class from which to derive scripted events.
    """
    def __init__(self, name, disruptive=False, exempt=None, location=None, owner=None):
        super(Event, self).__init__(name, location, owner)
        with locks.authority_of(locks.SYSTEM):
            self.type = 'event'
        self.disruptive = disruptive
        self.name = name
        self.locks.exempt = locks.Is(exempt)

    def trigger(self, event_source, trigger_source, **kwargs):
        if self.disruptive:
            raise CancelExecutionException("Triggered a disruptive event")


class VisibleEvent(Event):
    """
    An event which includes notices to be displayed when triggered
    """
    def __init__(self, name, emit=None, send=None, disruptive=False, exempt=None, location=None, owner=None):
        if not (emit or send):
            raise utils.UserError("One of emit message or send message is required.")
        super(VisibleEvent, self).__init__(name, disruptive=disruptive, exempt=exempt,
            location=location, owner=owner)
        self.emit_string = emit
        self.send_string = send

    def trigger(self, event_source, trigger_source, **kwargs):
        # the logic here goes something like this:
        #   If there's a message for the triggering player, send it,
        #   then emit the world-visible message to every else, if there is one.
        #   If there's not a player message, just emit the world message to everyone.
        try:
           trigger_source.send(self.send_string.format(obj=event_source.name))
        except AttributeError:
            event_source.emit(self.emit_string.format(obj=event_source.name, trigger_source=trigger_source.name))
        else:
            try:
                event_source.emit(self.emit_string.format(obj=event_source.name,
                    trigger_source=trigger_source.name), exceptions=[trigger_source])
            except AttributeError:
                pass
        super(VisibleEvent, self).trigger(event_source, trigger_source)


class CancelExecutionException(Exception):
    """
    An exception used in scripted events to disrupt the triggering command.
    """
    def __init__(self, string=""):
        if string:
            self.msg = string

    def __str__(self):
        return self.msg



