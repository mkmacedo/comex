from PIL import Image

def make_pdf(lista, output_file):
    imagens = []
    imagem_inicial = Image.open(lista[0])
    
    for a in range(len(lista)-1):
        #print(lista[a+1])
        imagem = Image.open(lista[a+1])
        imagens.append(imagem)

    pdf1_filename = output_file
    imagem_inicial.save(pdf1_filename, "PDF" ,resolution=100.0, save_all=True, append_images=imagens)

    
