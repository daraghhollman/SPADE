import juno


dataDirectory = "/home/daraghhollman/Main/data/SPADE/"
timeFrame = ["2018-01-02T10:00:00", "2018-01-02T12:00:00"]

#juno.DownloadData("JAD-E", timeFrame, dataDirectory)

juno.LoadData("JAD-E", timeFrame, dataDirectory)
