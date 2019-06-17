class UnsupportedPackageFormatException(BaseException):
    pass


class MissingInputException(BaseException):
    pass


class MissingMetadataException(BaseException):
    pass


class MissingFileException(BaseException):
    pass


class NapdNotValidException(BaseException):
    pass


class MetadataValidationException(BaseException):
    pass


class ChecksumException(BaseException):
    pass


class InvalidVersionFormat(Exception):
    pass


class NoOSMFilesFound(BaseException):
    pass
