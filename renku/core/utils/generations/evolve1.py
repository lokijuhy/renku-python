from zope.generations.utility import findObjectsMatching

from renku.core.models.provenance.activity import ActivityCollection


def evolve(context):
    root = context.connection.root()
    for collection in findObjectsMatching(root, lambda x: isinstance(x, ActivityCollection)):
        collection._path = "abcdef"
