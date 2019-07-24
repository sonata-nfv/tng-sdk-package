from tngsdk.package.logger import TangoLogger
from tngsdk.package.packager.packager import EtsiPackager, TestPackager
from tngsdk.package.packager.tango_packager import TangoPackager
from tngsdk.package.packager.osm_packager import OsmPackager
from tngsdk.package.packager.onap_packager import OnapPackager
from tngsdk.package.packager.exeptions import \
    UnsupportedPackageFormatException

LOG = TangoLogger.getLogger(__name__)


class PackagerManager(object):

    def __init__(self):
        self._packager_list = list()

    def new_packager(self, args,
                     storage_backend=None,
                     pkg_format="eu.5gtango"):
        # select the right Packager for the given format
        packager_cls = None
        if pkg_format == "eu.5gtango":
            packager_cls = TangoPackager
        elif pkg_format == "eu.etsi":
            packager_cls = EtsiPackager
        elif pkg_format == "eu.etsi.osm":
            packager_cls = OsmPackager
        elif pkg_format == "eu.lf.onap":
            packager_cls = OnapPackager
        elif pkg_format == "test":
            packager_cls = TestPackager
        # check if we have a packager for the given format or abort
        if packager_cls is None:
            raise UnsupportedPackageFormatException(
                "Pkg. format: {} not supported.".format(pkg_format))
        p = packager_cls(args, storage_backend=storage_backend)
        # TODO cleanup after packaging has completed (memory leak!!!)
        self._packager_list.append(p)
        return p

    def get_packager(self, uuid):
        LOG.debug(self._packager_list)
        for p in self._packager_list:
            if str(p.uuid) == uuid:
                return p
        return None

    @property
    def packager_list(self):
        return self._packager_list


# have one global instance of the manager
PM = PackagerManager()
