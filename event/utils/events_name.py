MAJOR_NAMES = {
    5: "AccessControl",
}

MINOR_NAMES = {
    1: "AccessGranted",
    2: "AccessDenied",
    16: "FaceSnap",
    75: "FaceRecognitionSuccess",
    76: "FaceRecognitionFailed",
    101: "QRCodeScan",
    104: "MultiVerify",
}


def major_name(major):
    return MAJOR_NAMES.get(major, "UnknownMajor")


def minor_name(minor):
    return MINOR_NAMES.get(minor, "UnknownMinor")
