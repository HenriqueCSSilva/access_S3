import config
import pymysql
import pandas as pd
import sys
from access_S3 import *
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFileDialog,QMessageBox,QLabel
from PyQt5.QtWidgets import QWidget, QAction, QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem,QVBoxLayout,QInputDialog

from itertools import chain
from werkzeug.security import check_password_hash

#---------------------------------------------------
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtWidgets import QMessageBox, QTreeWidgetItem, QTreeWidget ,QTreeWidgetItemIterator


#from PyQt5.uic import loadUi


#conectando a S3
from config import BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
import boto3
from boto3.session import Session

session = Session(aws_access_key_id = AWS_ACCESS_KEY_ID,
                aws_secret_access_key= AWS_SECRET_ACCESS_KEY)
conn = pymysql.connect(host= config.host, port=3306, user=config.user,
        password=config.password, db=config.db)
cur = conn.cursor()
print('conectou')

class Principal(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        super().setupUi(self)
    
        self.btn_BuscarUsuario01.clicked.connect(self.buscaBanco)
        self.txt_usuario.setText('mhenrique@satel-sa.com')
        self.txt_senha.setText('410569')
        self.btn_ListarPastas.clicked.connect(lambda: self.listarPastas(self.ddl_pasta.currentText() + '/'))

        self.treeWidget.itemExpanded.connect(lambda: self.listarPastas('TI/PLANILHAS/'))

        self.wdg_files.topLevelItem(0).setText(0,("teste"))

        self.wdg_files.topLevelItem(0).child(0).setText(0, ("teste001"))
        self.wdg_files.topLevelItem(0).child(1).setText(0, ("teste002"))
        lista = ['item', 'OutroItem']
        for item in lista:
            a = QTreeWidgetItem([item])
            #self.wdg_files.addTopLevelItem(a)


        
#----------------------------------------------------------------------------------

    def buscaBanco(self):
        self.ddl_pasta.clear()
        conn = pymysql.connect(host= config.host, port=3306, user=config.user,
        password=config.password, db=config.db)
        cur = conn.cursor()
        nomeUsuario = self.txt_usuario.text()

        try:
            email = self.txt_usuario.text()
            #select1 = ele busca o nome do usuario, email, nome do setor e número do setor
            sql_Select = (f"SELECT users.name, users.email, setor.nome, users.setor, users.password FROM satelp03_db_portal.users left join satelp03_db_portal.setor on satelp03_db_portal.users.setor = satelp03_db_portal.setor.id where users.email = '{email}'")
            tabela = pd.read_sql(sql_Select,conn)
            lista = tabela.values.tolist()  #transforma em lista
            nomedeUsuario = str(lista[0][0])  #Nome completo do usuario
            emaildoUsuario = str(lista[0][1]) #Email do usuario
            nomeSetordoUsuario = str(lista[0][2]) #Nome do setor dele
            numeroSetorUsuario = str(lista[0][3]) #Número correspondente ao setor dele
            senhadoUsuario = str(lista[0][4])
            verificarSenha = check_password_hash(senhadoUsuario,self.txt_senha.text())

            if verificarSenha == True:
                self.lbl_NomeUsuario.setText(nomedeUsuario)
                self.lbl_setor.setText(nomeSetordoUsuario)
    
                # select3 = busca se o usuário tem acesso extra e se tiver quais pastas são
                sql_Select3 =(f"SELECT setor FROM satelp03_db_portal.permissao where email='{emaildoUsuario}' ")
                tabela3 = pd.read_sql(sql_Select3, conn)
                lista3 = tabela3.values.tolist()  #lista de setores extras que o usuário tem
                #print('\n',lista3)
                pastasExtras = list(chain(*lista3))

                if not pastasExtras : #verifica se a lista de setores extras está vazio, se o usuário nao tem nenhuma permissao extra
                    sql_Select2 = (f"SELECT nome FROM satelp03_db_portal.nome_pastas where setor = '{numeroSetorUsuario}'")  #select2 = pega a pasta padrão do usuario
                    tabela2 = pd.read_sql(sql_Select2, conn)
                    lista2 = tabela2.values.tolist()
                    permissaoPadrao = str(lista2[0][0])
                    self.ddl_pasta.addItem(permissaoPadrao)
                else:
                    for x in pastasExtras: #percorre a lista de setores que o usuário tem permissão
                        sql_Select4 = (f"SELECT nome FROM satelp03_db_portal.nome_pastas where setor = '{x}'") #select4 = pega as pastas extras do usuario
                        tabela4 = pd.read_sql(sql_Select4, conn)
                        lista4 = tabela4.values.tolist()
                        permissaoExtra = str(lista4[0][0])
                        self.ddl_pasta.addItem(permissaoExtra)  #incremenda cada elemento da lista no select
                self.groupBox.setEnabled(True)
            else:
                self.groupBox.setEnabled(False)
                QMessageBox.about(self, "Atenção", "Senha inválida, por favor tente novamente!")
                self.lbl_NomeUsuario.setText('Senha Inválida')
                self.lbl_setor.setText('Senha Inválida')
                self.ddl_pasta.addItem('Senha Inválida')

        #se não achar o usuário no banco
        except Exception as erro:
            self.groupBox.setEnabled(False)
            QMessageBox.about(self, "Atenção", "Usuário Inválido, por favor tente novamente!")
            self.lbl_NomeUsuario.setText('Usuário Inválido')
            #self.txt_Setor.setText('Inválido')
            self.lbl_setor.setText('Usuário Inválido')
            self.ddl_pasta.addItem('Usuário Inválido')
            print(erro)



    def listarPastas(self, pasta):

        def list_folders(prefixo):
            s3 = session.client('s3')
            contents = []
            result = s3.list_objects(Bucket=BUCKET, Prefix=prefixo, Delimiter='/')
            try:
                for o in result.get('CommonPrefixes'):
                    contents.append(o.get('Prefix'))
            except:
                contents.append("Vazio")
            return contents

        def list_files(prefixo):
            s3 = session.client('s3')
            contents = []
            for item in s3.list_objects(Bucket=BUCKET, Prefix=prefixo, Delimiter='/')['Contents']:
                texto = item['Key']
                if texto != prefixo:
                    contents.append(texto)
            return contents

        s3 = session.client('s3')
        ext = ('.pdf', '.xls', '.xlsx', '.docx', '.ctb', '.dwt', '.doc', '.rar', '.cad', '.exe', '.dwg', '.png', '.jpg',
               '.JPG', '.jpeg', '.zip', 'tif', '.tiff', '.txt', '.7z', '.msi', '.bak', '.db')
        contents = list_folders(pasta)
        if contents[0] == 'Vazio':
            contents = list_files(pasta)
        else:
            contents = contents + list_files(pasta)
        print(contents)


# Parte Obrigatoria
if __name__ == '__main__':
    qt = QApplication(sys.argv)
    principal = Principal()
    principal.show()
    qt.exec_()