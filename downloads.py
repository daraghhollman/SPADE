import requests
import os

class Downloader:
    def __init__(self):
        pass


    def DownloadData(self, url, path):
        response = requests.get(url)

        if response.status_code == 200:
            with open(path, "wb") as file:
                file.write(response.content)

        else:
            raise Exception(f"Failed to download data from {url}")


class JunoDownloader(Downloader):
    def __init__(self, downloadDirectory: str):
        self.downloadDirectory = downloadDirectory


    def DownloadInstrumentData(self, instrument: str, date_yyyydoy: str):
        """Possible instruments include MAG, ..."""
        
        match instrument:
            
            case "MAG":
                downloadPath = f"https://pds-ppi.igpp.ucla.edu/ditdos/write?id=JNO-J-3-FGM-CAL-V1.0:FGM_JNO_L3_{date_yyyydoy}PC_R1S:fgm_jno_l3_{date_yyyydoy}pc_r1s_v01.sts&f=csv"

                # Check if MAG directory exists
                if not os.path.isdir(f"{self.downloadDirectory}MAG/"):
                    os.mkdir(f"{self.downloadDirectory}MAG/")

                super().DownloadData(downloadPath, f"{self.downloadDirectory}MAG/JunoMAG_{date_yyyydoy}.csv")
