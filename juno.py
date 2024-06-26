"""
THIS FILE WILL HANDLE THE FOLLOWING FOR THE JUNO SPACECRAFT:
    - DATA DOWNLOADING
    - DATA PROCESSING
    - PLOTTING
"""

import os
import requests
import astropy.time
from tqdm import tqdm

import tools
import pdsBinaryTools


class Downloader:

    def __init__(self, urls: list[str], downloadDirectory: str) -> None:
        self.urls = urls
        self.downloadDirectory = downloadDirectory

        if not os.path.exists(self.downloadDirectory):
            print(f"Creating directory {downloadDirectory}")
            os.mkdir(downloadDirectory)

    def Download(self) -> None:
        """
        Downloads files from the urls to the download directory.
        """

        for url in self.urls:
            print(f"Attempting to download: {url.split('/')[-1]}")
            response = requests.get(url, stream=True, timeout=10)

            with open(self.downloadDirectory + url.split("/")[-1], "wb") as f:
                for chunk in tqdm(response.iter_content(chunk_size=1024)):
                    if chunk:
                        f.write(chunk)


def DownloadData(instrument: str, timeFrame: list[str], dataDirectory: str) -> None:
    """

    Valid instruments: MAG, Waves, JAD-E, JAD-I, JEDI

    """

    validInstuments = ["MAG", "Waves", "JAD-E", "JAD-I", "JEDI"]

    if instrument not in validInstuments:
        raise ValueError(
            f"Instrument: '{instrument}' is not a valid choice for the Juno spacecraft"
        )

    # Perform data downloads
    match instrument:

        case "JAD-E":
            # Downloading JAD Electrons data from the PDS
            # JAD-E files comprise of binary data files and label files required to parse the binary
            # There are two possible resolutions, we download both resolutions if both exist
            # to stich them together later.
            pdsUrl = GetPdsUrl("JAD-E")

            binaryPaths = [
                f"{pdsUrl}{pathAddition}"
                for pathAddition in tools.PathsFromTimeDifference(
                    timeFrame[0],
                    timeFrame[1],
                    "%Y/%Y%j/ELECTRONS/JAD_L50_HRS_ELC_TWO_DEF_%Y%j_V01.DAT",
                )
            ]
            # include low res paths
            binaryPaths += [
                f"{pdsUrl}{pathAddition}"
                for pathAddition in tools.PathsFromTimeDifference(
                    timeFrame[0],
                    timeFrame[1],
                    "%Y/%Y%j/ELECTRONS/JAD_L50_LRS_ELC_ANY_DEF_%Y%j_V01.DAT",
                )
            ]

            labelPaths = [
                f"{pdsUrl}{pathAddition}"
                for pathAddition in tools.PathsFromTimeDifference(
                    timeFrame[0],
                    timeFrame[1],
                    "%Y/%Y%j/ELECTRONS/JAD_L50_HRS_ELC_TWO_DEF_%Y%j_V01.LBL",
                )
            ]

            labelPaths += [
                f"{pdsUrl}{pathAddition}"
                for pathAddition in tools.PathsFromTimeDifference(
                    timeFrame[0],
                    timeFrame[1],
                    "%Y/%Y%j/ELECTRONS/JAD_L50_LRS_ELC_ANY_DEF_%Y%j_V01.LBL",
                )
            ]

            downloadDirectory = os.path.join(dataDirectory, "JAD-E/")

            downloader = Downloader(labelPaths + binaryPaths, downloadDirectory)
            downloader.Download()

            # We must now delete the empty files where the resolution asked for doesn't exist
            # This occurs frequently as most days are in low res mode only
            # Better practice long term would be do detect this before saving the file
            # but I could not find a way to successful do this for these files yet.
            # Empty files will be < 200 bytes
            tools.DeleteEmptyFiles(downloadDirectory, 200)


def GetPdsUrl(instrument: str) -> str:
    """
    A function to return the correct base url for a given instrument
    """

    match instrument:
        case "JAD-E":
            return (
                "https://search-pdsppi.igpp.ucla.edu/ditdos/download?id="
                "pds://PPI/JNO-J_SW-JAD-5-CALIBRATED-V1.0/DATA/"
            )

    raise ValueError("Invalid Instrument Choice")


def LoadData(instrument: str, timeFrame: list[str], dataDirectory: str):
    """
    Loads data from a specific instrument
    """
    match instrument:
        case "JAD-E":
            LoadJadEData(timeFrame, dataDirectory)


def LoadJadEData(timeFrame: list[str], dataDirectory: str):

    # First we load all JAD-E files from the data directory
    allFiles = os.listdir(os.path.join(dataDirectory, "JAD-E/"))
    jadEFiles = [f for f in allFiles if "JAD_L50" in f and "ELC" in f]

    binaryFiles = [
        os.path.join(dataDirectory, "JAD-E/", f)
        for f in jadEFiles
        if f.endswith(".DAT")
    ]
    labelFiles = [
        os.path.join(dataDirectory, "JAD-E/", f)
        for f in jadEFiles
        if f.endswith(".LBL")
    ]

    binaryFiles.sort()
    labelFiles.sort()

    multiDayData = []

    for labelFile, binaryFile in zip(labelFiles, binaryFiles):

        # Read files using routines from pdsBinaryTools.py
        labelInfo, structClass = pdsBinaryTools.ReadLabel(labelFile)
        data = pdsBinaryTools.ReadBinary(binaryFile, structClass, labelInfo)

        multiDayData.append(data)

    # We need to shorted the data to match the timeframe specified

    newData = {"startTime": [], "endTime": [], "electrons": [], "pitchAngles": []}

    print("Shortening data to match time frame...")
    for i, data in enumerate(multiDayData):

        if i == 0 and i == len(multiDayData) - 1:
            # Only one file / day loaded
            sliceStartIndex = 0
            sliceEndIndex = 0

            for j, time in enumerate(data["startTime"]):

                # Deal with formatting stuff
                timeStep = astropy.time.Time(time, format="isot")
                timeStep.format = "datetime"

                timeFrameStart = astropy.time.Time(timeFrame[0], format="isot")
                timeFrameStart.format = "datetime"

                if timeStep >= timeFrameStart:
                    break

                sliceStartIndex = j + 1

            for j, time in enumerate(data["startTime"]):

                # Deal with formatting stuff
                timeStep = astropy.time.Time(time, format="isot")
                timeStep.format = "datetime"

                timeFrameEnd = astropy.time.Time(timeFrame[1], format="isot")
                timeFrameEnd.format = "datetime"

                if timeStep >= timeFrameEnd:
                    break

                sliceEndIndex = j

            if sliceStartIndex == sliceEndIndex:
                raise RuntimeError(
                    "Timeframe start point and end point are closer than timestep in JADE data"
                )

            # Construct new data which is cropped to the time frame
            newData = {
                "startTime": data["startTime"][sliceStartIndex:sliceEndIndex],
                "endTime": data["endTime"][sliceStartIndex:sliceEndIndex],
                "electrons": data["data"][sliceStartIndex:sliceEndIndex],
                "pitchAngles": data["pitch angle scale"][sliceStartIndex:sliceEndIndex],
            }

        # We importantly also need to handle the cases for where there are multiple files
        # Starting file:
        elif i == 0:
            sliceStartIndex = 0

            for j, time in enumerate(data["startTime"]):

                # Deal with formatting stuff
                timeStep = astropy.time.Time(time, format="isot")
                timeStep.format = "datetime"

                timeFrameStart = astropy.time.Time(timeFrame[0], format="isot")
                timeFrameStart.format = "datetime"

                if timeStep >= timeFrameStart:
                    break

                sliceStartIndex = j + 1

            newData["startTime"].extend(data["startTime"][sliceStartIndex:])
            newData["endTime"].extend(data["endTime"][sliceStartIndex:])
            newData["electrons"].extend(data["data"][sliceStartIndex:])
            newData["pitchAngles"].extend(data["pitch angle scale"][sliceStartIndex:])

        # Ending file:
        elif i == len(multiDayData) - 1:
            sliceEndIndex = 0

            for j, time in enumerate(data["startTime"]):

                # Deal with formatting stuff
                timeStep = astropy.time.Time(time, format="isot")
                timeStep.format = "datetime"

                timeFrameEnd = astropy.time.Time(timeFrame[1], format="isot")
                timeFrameEnd.format = "datetime"

                if timeStep >= timeFrameEnd:
                    break

                sliceEndIndex = j

            newData["startTime"].extend(data["startTime"][sliceEndIndex:])
            newData["endTime"].extend(data["endTime"][sliceEndIndex:])
            newData["electrons"].extend(data["data"][sliceEndIndex:])
            newData["pitchAngles"].extend(data["pitch angle scale"][sliceEndIndex:])

        # File is in the middle
        else:
            newData["startTime"].extend(data["startTime"])
            newData["endTime"].extend(data["endTime"])
            newData["electrons"].extend(data["data"])
            newData["pitchAngles"].extend(data["pitch angle scale"])


    # We have now concatinated the data but need to perform pre-processing
    timeFmt = "%Y-%m-%dT%H:%M:%S.%f"
