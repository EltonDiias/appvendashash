from kivy.app import App
from kivy.lang import Builder
from telas import *
from botoes import *
import requests
from bannervenda import BannerVenda
import os
from functools import partial
from myfirebase import MyFirebase
from bannervendedor import BannerVendedor
from datetime import date

GUI = Builder.load_file('main.kv')


class MainApp(App):

    cliente = None
    produto = None
    unidade = None

    def build(self):
        self.firebase = MyFirebase()
        return GUI

    def on_start(self):
        # carregar as fotos de perfil
        arquivos = os.listdir("icones/fotos_perfil")
        pagina_foto_perfil = self.root.ids['fotoperfilpage']
        lista_fotos = pagina_foto_perfil.ids['lista_fotos_perfil']
        for foto in arquivos:
            imagem = ImageButton(source=f'icones/fotos_perfil/{foto}', on_release=partial(self.mudar_foto_perfil, foto))
            lista_fotos.add_widget(imagem)

        # carregar as fotos dos clientes
        arquivos_cliente = os.listdir("icones/fotos_clientes")
        pagina_adicionarvendas = self.root.ids['adicionarvendaspage']
        lista_clientes = pagina_adicionarvendas.ids['lista_clientes']
        for foto_cliente in arquivos_cliente:
            imagem = ImageButton(source=f'icones/fotos_clientes/{foto_cliente}',
                                 on_release=partial(self.selecionar_cliente, foto_cliente))
            label = LabelButton(text=foto_cliente[:-4].capitalize(),
                                on_release=partial(self.selecionar_cliente, foto_cliente))
            lista_clientes.add_widget(imagem)
            lista_clientes.add_widget(label)

        # carregar as fotos dos produtos
        arquivos_produtos = os.listdir("icones/fotos_produtos")
        pagina_adicionarvendas = self.root.ids['adicionarvendaspage']
        lista_produtos = pagina_adicionarvendas.ids['lista_produtos']
        for foto_produto in arquivos_produtos:
            imagem = ImageButton(source=f'icones/fotos_produtos/{foto_produto}',
                                 on_release=partial(self.selecionar_produto, foto_produto))
            label = LabelButton(text=foto_produto[:-4].capitalize(),
                                on_release=partial(self.selecionar_produto, foto_produto))
            lista_produtos.add_widget(imagem)
            lista_produtos.add_widget(label)

        # carregar a data
        data = pagina_adicionarvendas.ids['label_data']
        data.text = f"Data: {date.today().strftime('%d/%m/%Y')}"
        # carrega as infos do usuario
        self.carregar_info_usuario()

    def carregar_info_usuario(self):

        try:
            with open("refreshtoken.txt", "r") as arquivo:
                refresh_token = arquivo.read()
            local_id, id_token = self.firebase.trocar_token(refresh_token)
            self.local_id = local_id
            self.id_token = id_token

            # pegar informações do usuario
            requisicao = requests.get(
                f'https://aplicativovendashash-6c768-default-rtdb.firebaseio.com/{self.local_id}.json'
                f'?auth={self.id_token}')
            requisicao_dic = requisicao.json()

            # preencher foto de perfil
            avatar = requisicao_dic['avatar']
            self.avatar = avatar
            foto_perfil = self.root.ids['foto_perfil']
            foto_perfil.source = f"icones/fotos_perfil/{avatar}"

            # preencher o id unico
            id_vendedor = requisicao_dic['id_vendedor']
            self.id_vendedor = id_vendedor
            pagina_ajuste = self.root.ids['ajustespage']
            pagina_ajuste.ids['id_vendedor'].text = f"Seu id único: {id_vendedor}"

            # total de vendas
            total_vendas = float(requisicao_dic['total_vendas'])
            self.total_vendas = total_vendas
            homepage = self.root.ids['homepage']
            homepage.ids['label_total_vendas'].text = f"[color=#000000]Total de Vendas:[/color] [b]R${total_vendas}[/b]"

            # equipe do usuario
            self.equipe = requisicao_dic['equipe']

            # preencher lista de vendas
            try:
                vendas = requisicao_dic['vendas']
                self.vendas = vendas
                pagina_homepage = self.root.ids['homepage']
                lista_vendas = pagina_homepage.ids['lista_vendas']
                for id_venda in vendas:
                    venda = vendas[id_venda]
                    banner = BannerVenda(cliente=venda['cliente'], data=venda['data'], foto_cliente=venda['foto_cliente'],
                                         foto_produto=venda['foto_produto'], preco=venda['preco'], produto=venda['produto'],
                                         quantidade=venda['quantidade'], unidade=venda['unidade'])
                    lista_vendas.add_widget(banner)
            except Exception as erro:
                print(erro)

            # ->preencher equipe de vendedores
            equipe = requisicao_dic['equipe']
            lista_equipe = equipe.split(",")
            pagina_listavendedores = self.root.ids['listarvendedorespage']
            lista_vendedores = pagina_listavendedores.ids['lista_vendedores']

            for id_vendedor_equipe in lista_equipe:
                if id_vendedor_equipe != "":
                    banner_vendedor = BannerVendedor(id_vendedor=id_vendedor_equipe)
                    lista_vendedores.add_widget(banner_vendedor)

            self.mudar_tela("homepage")
        except:
            pass

    def mudar_tela(self, id_tela):
        gerenciador_telas = self.root.ids['screen_manager']
        gerenciador_telas.current = id_tela

    def mudar_foto_perfil(self, foto, *args):
        foto_perfil = self.root.ids['foto_perfil']
        foto_perfil.source = f"icones/fotos_perfil/{foto}"

        info = "{" + f'"avatar": "{foto}"' + "}"
        requisicao = requests.patch(f"https://aplicativovendashash-6c768-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}",
                                    data=info)

        self.mudar_tela("ajustespage")

    def adicionar_vendedor(self, id_vendedor_adicionado):
        link = f'https://aplicativovendashash-6c768-default-rtdb.firebaseio.com/.json?orderBy=' \
               f'"id_vendedor"&equalTo="{id_vendedor_adicionado}"'
        requisicao = requests.get(link)
        requisicao_dic = requisicao.json()

        page_add_vendedor = self.root.ids['adicionarvendedorpage']
        label_mensagem = page_add_vendedor.ids['mensagem_outrovendedor']

        if requisicao_dic == {}:
            label_mensagem.text = "Usuário não encontrado!"
        else:
            equipe = self.equipe.split(',')
            if id_vendedor_adicionado in equipe:
                label_mensagem.text = "Vendedor já faz parte da equipe!"
            else:
                self.equipe = self.equipe + f",{id_vendedor_adicionado}"
                info = f'{{"equipe": "{self.equipe}"}}'
                requests.patch(f'https://aplicativovendashash-6c768-default-rtdb.firebaseio.com/{self.local_id}.json?'
                               f'auth={self.id_token}', data=info)
                label_mensagem.text = "Vendedor Adicionado com Sucesso"
                # adicionar banner do vendedor adicionado
                pagina_listavendedores = self.root.ids['listarvendedorespage']
                lista_vendedores = pagina_listavendedores.ids['lista_vendedores']
                banner_vendedor = BannerVendedor(id_vendedor=id_vendedor_adicionado)
                lista_vendedores.add_widget(banner_vendedor)

    def selecionar_cliente(self, foto, *args):
        self.cliente = foto.replace(".png", "")
        # pintar de branco todos os itens
        pagina_adicionarvendas = self.root.ids['adicionarvendaspage']
        lista_clientes = pagina_adicionarvendas.ids['lista_clientes']
        for item in list(lista_clientes.children):
            item.color = (1, 1, 1, 1)
            # pintar de azul o texto do item selecionado

            # foto -> carrefour.png
            try:
                texto = item.text
                texto = texto.lower() + ".png"
                if foto == texto:
                    item.color = (0, 207/255, 219/255, 1)

            except:
                pass

    def selecionar_produto(self, foto, *args):
        self.produto = foto.replace(".png", "")
        # pintar de branco todos os itens
        pagina_adicionarvendas = self.root.ids['adicionarvendaspage']
        lista_produtos = pagina_adicionarvendas.ids['lista_produtos']
        for item in list(lista_produtos.children):
            item.color = (1, 1, 1, 1)
            # pintar de azul o texto do item selecionado
            try:
                texto = item.text
                texto = texto.lower() + ".png"
                if foto == texto:
                    item.color = (0, 207/255, 219/255, 1)
            except:
                pass

    def selecionar_unidade(self, id_label, *args):
        self.unidade = id_label.replace("unidades_", "")
        pagina_adicionarvendas = self.root.ids['adicionarvendaspage']

        # pintar todo o mundo de branco
        pagina_adicionarvendas.ids['unidades_kg'].color = (1, 1, 1, 1)
        pagina_adicionarvendas.ids['unidades_unidades'].color = (1, 1, 1, 1)
        pagina_adicionarvendas.ids['unidades_litros'].color = (1, 1, 1, 1)

        # pintar o cara selecionado de azul
        pagina_adicionarvendas.ids[id_label].color = (0, 207/255, 219/255, 1)

    def adicionar_venda(self):
        cliente = self.cliente
        produto = self.produto
        unidade = self.unidade

        pagina_adicionar_vendas = self.root.ids['adicionarvendaspage']
        data = pagina_adicionar_vendas.ids['label_data'].text.replace("Data: ", "")
        preco = pagina_adicionar_vendas.ids['preco_total'].text
        quantidade = pagina_adicionar_vendas.ids['quantidade'].text

        if not cliente:
            pagina_adicionar_vendas.ids['label_sel_cliente'].color = (1, 0, 0, 1)
        if not produto:
            pagina_adicionar_vendas.ids['label_sel_prod'].color = (1, 0, 0, 1)
        if not unidade:
            pagina_adicionar_vendas.ids['unidades_kg'].color = (1, 0, 0, 1)
            pagina_adicionar_vendas.ids['unidades_unidades'].color = (1, 0, 0, 1)
            pagina_adicionar_vendas.ids['unidades_litros'].color = (1, 0, 0, 1)
        if not preco:
            pagina_adicionar_vendas.ids['label_preco'].color = (1, 0, 0, 1)
        else:
            try:
                preco = float(preco)
            except:
                pagina_adicionar_vendas.ids['label_preco'].color = (1, 0, 0, 1)
        if not quantidade:
            pagina_adicionar_vendas.ids['label_quantidade'].color = (1, 0, 0, 1)
        else:
            try:
                quantidade = float(quantidade)
            except:
                pagina_adicionar_vendas.ids['label_quantidade'].color = (1, 0, 0, 1)

        # dado que tudo foi preenchido...
        if cliente and produto and unidade and quantidade and (type(preco) == float) and (type(quantidade)) == float:
            foto_produto = produto + ".png"
            foto_cliente = cliente + ".png"

            info = f'{{"cliente": "{cliente}", "produto": "{produto}", "foto_cliente": "{foto_cliente}",' \
                   f' "foto_produto": "{foto_produto}", "data": "{data}", "unidade": "{unidade}", "preco": "{preco}",' \
                   f' "quantidade": "{quantidade}"}}'

            requests.post(f'https://aplicativovendashash-6c768-default-rtdb.firebaseio.com/{self.local_id}'
                          f'/vendas.json?auth={self.id_token}', data=info)

            banner = BannerVenda(cliente=cliente, data=data, foto_cliente=foto_cliente, foto_produto=foto_produto,
                                 preco=preco, produto=produto, quantidade=quantidade, unidade=unidade)
            pagina_homepage = self.root.ids['homepage']
            lista_vendas = pagina_homepage.ids['lista_vendas']
            lista_vendas.add_widget(banner)
            try:
                requisicao = requests.get(f"https://aplicativovendashash-6c768-default-rtdb.firebaseio.com/"
                                          f"{self.local_id}/total_vendas.json?auth={self.id_token}")
                total_vendas = float(requisicao.json())
                total_vendas += preco
                info = f'{{"total_vendas": "{total_vendas}"}}'
                requests.patch(f"https://aplicativovendashash-6c768-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}",
                               data=info)
                homepage = self.root.ids['homepage']
                homepage.ids['label_total_vendas'].text = f"[color=#000000]Total de Vendas:[/color] [b]R${total_vendas}[/b]"
            except Exception as erro:
                print(erro)
            self.mudar_tela("homepage")


        self.cliente = None
        self.produto = None
        self.unidade = None

    def carregar_todas_vendas(self):
        pagina_todasasvendas = self.root.ids['todasvendaspage']
        lista_vendas = pagina_todasasvendas.ids['lista_vendas']
        for item in list(lista_vendas.children):
            lista_vendas.remove_widget(item)
        # preencher a pagina todasvendaspage
        # pegar informações da empresa
        requisicao = requests.get(
            f'https://aplicativovendashash-6c768-default-rtdb.firebaseio.com/.json?orderBy="id_vendedor"')
        requisicao_dic = requisicao.json()

        # preencher foto de perfil
        foto_perfil = self.root.ids['foto_perfil']
        foto_perfil.source = f"icones/fotos_perfil/hash.png"

        total_vendas = 0
        for local_id_usuario in requisicao_dic:
            try:
                vendas = requisicao_dic[local_id_usuario]['vendas']
                for id_venda in vendas:
                    venda = vendas[id_venda]
                    banner = BannerVenda(cliente=venda['cliente'], data=venda['data'],
                                         foto_cliente=venda['foto_cliente'], foto_produto=venda['foto_produto'],
                                         preco=venda['preco'], produto=venda['produto'], quantidade=venda['quantidade'],
                                         unidade=venda['unidade'])
                    total_vendas += float(venda['preco'])
                    lista_vendas.add_widget(banner)
            except Exception as erro:
                print(erro)

        # total de vendas

        pagina_todasasvendas.ids['label_total_vendas'].text = f"[color=#000000]Total de Vendas:[/color] [b]R${total_vendas}[/b]"

        # redirecionar para a pagina todasvendaspage
        self.mudar_tela("todasvendaspage")

    def sair_todasasvendas(self, id_tela):
        # preencher foto de perfil
        foto_perfil = self.root.ids['foto_perfil']
        foto_perfil.source = f"icones/fotos_perfil/{self.avatar}"
        self.mudar_tela(id_tela)

    def carregar_vendas_vendedor(self, dic_infos_vendedor, *args):

        pag_outrovendedor = self.root.ids['vendasoutrovendedorpage']
        lista_vendas = pag_outrovendedor.ids['lista_vendas']
        try:
            vendas = dic_infos_vendedor["vendas"]
            # limpar vendas anteriores
            for item in list(lista_vendas.children):
                lista_vendas.remove_widget(item)

            for id_venda in vendas:
                venda = vendas[id_venda]
                banner = BannerVenda(cliente=venda['cliente'], data=venda['data'],
                                     foto_cliente=venda['foto_cliente'], foto_produto=venda['foto_produto'],
                                     preco=venda['preco'], produto=venda['produto'], quantidade=venda['quantidade'],
                                     unidade=venda['unidade'])
                lista_vendas.add_widget(banner)
        except Exception as erro:
            print(erro)
        total_vendas = dic_infos_vendedor['total_vendas']
        pag_outrovendedor.ids['label_total_vendas'].text = f"[color=#000000]Total de Vendas:[/color] [b]R${total_vendas}[/b]"

        # preencher foto de perfil
        foto_perfil = self.root.ids['foto_perfil']
        avatar = dic_infos_vendedor['avatar']
        foto_perfil.source = f"icones/fotos_perfil/{avatar}"

        self.mudar_tela("vendasoutrovendedorpage")


MainApp().run()