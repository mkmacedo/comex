# import module
from pdf2image import convert_from_path
 
def convertPDF2Image(filename, dimensions=None):
  # Store Pdf with convert_from_path function
  if dimensions == None:
    images = convert_from_path(filename)
  
  else:
    images = convert_from_path(filename, size=dimensions)
  
  filenames = []
  
  for i in range(len(images)):
    # Save pages as images in the pdf
    output_name = filename[:filename.find('.pdf')] + str((lambda x: '' if x == 0 else '_'+str(x))(i))+'.jpg'
    images[i].save(output_name, 'JPEG')
    filenames.append(output_name)
  
  if len(filenames) > 1:
    return filenames
  
  else:
    return filenames[0]
  

#a = convertPDF2Image('Diremadi.pdf')
#print(a)