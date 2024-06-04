import downloads

downloader = downloads.JunoDownloader("../data/SPADE/")

downloader.DownloadInstrumentData("MAG", "2016209")
