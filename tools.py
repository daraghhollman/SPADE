# A SET OF AUXILLARY TOOLS FOR SPADE

import datetime
import os

def DateRange(startDate, endDate):
    """

    Returns the dates between two input dates

    """
    for n in range(int((endDate - startDate).days) + 1): # NOTE: adding +1 to include endDate
        yield startDate + datetime.timedelta(n)


def PathsFromTimeDifference(t1, t2, pathFormat):
    """

    Creates path names between two times in a specified format 

    Arguments:
    t1, t2 -- (str) Input times between which the paths will be created. Must be in the format "YYYY-MM-DDThh:mm:ss"
    pathFormat -- (str) Path format which the files to be downloaded are in

    Returns:
    A list of the paths following the pathFormat. One path for each day between t1 and t2

    """
    date1, _ = t1.split("T")
    date2, _ = t2.split("T")

    year1, month1, day1 = date1.split("-")
    year2, month2, day2 = date2.split("-")

    startDate = datetime.date(int(year1), int(month1), int(day1)) 
    endDate = datetime.date(int(year2), int(month2), int(day2))

    pathExtensions = []

    if startDate == endDate:
        pathExtensions.append(startDate.strftime(pathFormat))
    
    else:
        for date in DateRange(startDate, endDate):
            pathExtension = date.strftime(pathFormat)
            pathExtensions.append(pathExtension)

    return pathExtensions


def DeleteEmptyFiles(directory: str, bytesThreshold: int):
    """
    Deletes files in a given directory which are below a size threshold.
    """

    for file in os.listdir(directory):
        filePath = os.path.join(directory, file)

        if os.path.getsize(filePath) < bytesThreshold:
            os.remove(filePath)
