from PyPDF2 import PdfFileWriter, PdfFileReader
#import sys

#file = sys.argv[1]

def splitPDF(filename):
    inputpdf = PdfFileReader(open(filename, "rb"))

    outputFiles = []

    for i in range(inputpdf.numPages):
        output = PdfFileWriter()
        output.addPage(inputpdf.getPage(i))

        output_file = filename[:filename.find('.pdf')] +'_'+ str(i)+'.pdf'
        with open(output_file, "wb") as outputStream:
            output.write(outputStream)

        outputFiles.append(output_file)

    return outputFiles

#files = splitPDF(file)
#print(files)