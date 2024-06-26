"""
THIS FILE WILL HANDLE THE FOLLOWING FOR THE JUNO SPACECRAFT:
    - DATA DOWNLOADING
    - DATA PROCESSING
    - PLOTTING
"""

import os
import requests
from tqdm import tqdm

import tools


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
            return "https://search-pdsppi.igpp.ucla.edu/ditdos/download?id=pds://PPI/JNO-J_SW-JAD-5-CALIBRATED-V1.0/DATA/"

    raise ValueError("Invalid Instrument Choice")
