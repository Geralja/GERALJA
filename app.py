# -*- coding: utf-8 -*-
import streamlit as st
import firebaseadmin
from firebaseadmin import credentials firestore
import base64
import json
import datetime
import math
import re
import time
import pandas as pd
import unicodedata
from streamlitjseval import streamlitjseval getgeolocation
import base64
def converterimgb64file
    if file is not None
        return base64b64encodefilegetvaluedecode
    return None
stsetpageconfigpagetitleGeral J layoutwide

stsetpageconfigpagetitleGeral J layoutwide

  CONFIGURAO DE TEMA MANUAL 
if temaclaro not in stsessionstate
    stsessionstatetemaclaro  False

 Interruptor no topo para o usurio consertar a tela se estiver preta
stsessionstatetemaclaro  sttoggle FORAR MODO CLARO Use se a tela estiver escura valuestsessionstatetemaclaro

if stsessionstatetemaclaro
    stmarkdown
        style
            stApp  backgroundcolor white important 
              color black important 
            stMarkdown p span label div  color black important 
            iframe  backgroundcolor white important 
            stButton button  backgroundcolor f0f2f6 important color black important border 1px solid ccc important 
            datatestidstExpander  backgroundcolor f9f9f9 important border 1px solid ddd important 
            input  backgroundcolor white important color black important border 1px solid ccc important 
        style
     unsafeallowhtmlTrue

  seus outros imports firebase base64 etc

stsetpageconfigpagetitleGeral J layoutwide

  COLOQUE AQUI CSS PARA CORRIGIR O MODO ESCURO E CLARO 
stmarkdown
    style
         Fora o preenchimento no topo 
        divblockcontainer paddingtop2rem
        
         Garante que os cards HTML se adaptem ao tema 
        metriccard 
            border 1px solid 555 
            borderradius 10px 
            padding 10px 
            textalign center
            marginbottom 10px
        
    style
 unsafeallowhtmlTrue

 CSS para evitar que o fundo fique preto por erro de renderizao
stmarkdown
    style
    stApp 
        backgroundcolor white
    
    datatestidstExpander 
        backgroundcolor ffffff important
        border 1px solid f0f2f6
    
    style
 unsafeallowhtmlTrue
stsetpageconfigpagetitleGeralJ layoutwide

 Remove o menu superior o rodap Made with Streamlit e o boto de Deploy
stmarkdown
    style
    MainMenu visibility hidden
    footer visibility hidden
    header visibility hidden
    header display none important
    style
 unsafeallowhtmlTrue

 
 1 CONFIGURAO DE AMBIENTE E PERFORMANCE
 
stsetpageconfig
    pagetitleGeralJ  Criando Solues
    pageicon
    layoutwide
    initialsidebarstatecollapsed


 
 2 CAMADA DE PERSISTNCIA FIREBASE
 
stcacheresource
def conectarbancomaster
    if not firebaseadminapps
        try
            if FIREBASEBASE64 not in stsecrets
                sterror Chave de segurana FIREBASEBASE64 no encontrada
                ststop
            b64key  stsecretsFIREBASEBASE64
            decodedjson  base64b64decodeb64keydecodeutf8
            creddict  jsonloadsdecodedjson
            cred  credentialsCertificatecreddict
            return firebaseadmininitializeappcred
        except Exception as e
            sterrorf FALHA NA INFRAESTRUTURA e
            ststop
    return firebaseadmingetapp

appengine  conectarbancomaster
db  firestoreclient
 
 
 3 POLTICAS E CONSTANTES
 
PIXOFICIAL  11991853488
ZAPADMIN  5511991853488
CHAVEADMIN  mumias
TAXACONTATO  1
BONUSWELCOME  5
LATREF  235505
LONREF  466333

CATEGORIASOFICIAIS  
    Academia Acompanhante de Idosos Aougue Adega Adestrador de Ces Advocacia Agropecuria 
    Ajudante Geral Animador de Festas Arquitetoa ArmarinhoAviamentos Assistncia Tcnica 
    Aulas Particulares Auto Eltrica Auto Peas Bab Nanny Banho e Tosa BarbeariaSalo 
    Barman  Bartender Bazar Borracheiro Cabeleireiroa Cafeteria Calados Carreto 
    Celulares Chaveiro Churrascaria Clnica Mdica Comida Japonesa Confeiteiroa 
    Contabilidade Costureira  Alfaiate Cozinheiroa Particular Cuidador de Idosos 
    Danarinoa  Entretenimento GogoboyGirl Decoradora de Festas Destaque de Eventos 
    Diarista  Faxineira Doceria Eletrodomsticos Eletricista Eletrnicos Encanador 
    Escola Infantil Esttica Automotiva Esttica Facial Esteticista Farmcia Fisioterapia 
    Fitness Floricultura Fotgrafoa Freteiro Fretista  Mudanas Funilaria e Pintura 
    Garom e garonete Gesseiro Guincho 24h Hamburgueria Hortifruti Idiomas Imobiliria 
    Informtica Instalador de Arcondicionado Internet de fibra ptica Jardineiro Joalheria 
    Lanchonete Lava Jato Lavagem de Sofs  Estofados Loja de Roupas Loja de Variedades 
    Madeireira Manicure e Pedicure Maquiadora Marceneiro Marido de Aluguel Material de Construo 
    Mecnico de Autos Montador de Mveis MotoboyEntregas Motorista Particular Mveis 
    Moto Peas Nutricionista Odontologia tica Outro Personalizado Padaria Papelaria 
    Passeador de Ces Dog Walker Pastelaria Pedreiro Pet Shop Pintor Piscineiro Pizzaria 
    Professora Particular Psicologia Recepcionista de Eventos Reforo Escolar Refrigerao 
    Relojoaria Salgadeiroa Segurana  Vigilante Seguros Som e Alarme Sorveteria 
    TatuagemPiercing Tcnico de Celular Tcnico de Fogo Tcnico de Geladeira Tcnico de Lavadora 
    Tcnico de NotebookPC Telhadista TI Tecnologia Tintas Veterinrioa Web Designer

 
 SUPER MOTOR DE INTELIGNCIA GERALJ  VERSO MEGA EXPANDIDA
 
CONCEITOSEXPANDIDOS  
      ALIMENTAO BARES E GASTRONOMIA 
    pizza Pizzaria pizzaria Pizzaria fome Pizzaria massa Pizzaria calzone Pizzaria
    lanche Lanchonete hamburguer Lanchonete burger Lanchonete xtudo Lanchonete hot dog Lanchonete cachorro quente Lanchonete salgado Lanchonete coxinha Lanchonete pastel Lanchonete
    comida Restaurante almoco Restaurante marmita Restaurante jantar Restaurante restaurante Restaurante self service Restaurante churrasco Restaurante espetinho Restaurante
    doce Confeitaria bolo Confeitaria festa Confeitaria salgadinho Confeitaria brigadeiro Confeitaria sobremesa Confeitaria aniversario Confeitaria
    pao Padaria padaria Padaria cafe Padaria padoca Padaria leite Padaria biscoito Padaria
    acai Aa cupuacu Aa sorvete Sorveteria picole Sorveteria gelateria Sorveteria
    cerveja Adega bebida Adega gelo Adega adega Adega vinho Adega destilado Adega vodka Adega refrigerante Adega
    churros Doceria crepe Doceria tapioca Lanchonete

      VAREJO MODA E PRESENTES 
    roupa Loja de Roupas vestuario Loja de Roupas moda Loja de Roupas camiseta Loja de Roupas calca Loja de Roupas blusa Loja de Roupas boutique Loja de Roupas brecho Loja de Roupas
    sapato Calados tenis Calados chinelo Calados sandalia Calados bota Calados sapataria Calados
    presente Loja de Variedades brinquedo Loja de Variedades utilidades Loja de Variedades papelaria Loja de Variedades caderno Loja de Variedades
    relogio Relojoaria joia Joalheria anel Joalheria brinco Joalheria
    otica tica oculos tica lente tica

      SADE BELEZA E BEMESTAR 
    remedio Farmcia farmacia Farmcia drogaria Farmcia saude Farmcia medicamento Farmcia
    cabelo BarbeariaSalo barba BarbeariaSalo corte BarbeariaSalo cabeleireiro BarbeariaSalo manicure BarbeariaSalo unha BarbeariaSalo pedicure BarbeariaSalo sobrancelha BarbeariaSalo maquiagem BarbeariaSalo
    academia Fitness treino Fitness musculacao Fitness crossfit Fitness suplemento Fitness
    dentista Odontologia dente Odontologia aparelho Odontologia

      TECNOLOGIA E ELETRODOMSTICOS 
    celular Assistncia Tcnica iphone Assistncia Tcnica tela Assistncia Tcnica carregador Assistncia Tcnica android Assistncia Tcnica bateria Assistncia Tcnica
    computador TI notebook TI formatar TI wifi TI internet TI pc TI gamer TI impressora TI
    geladeira Refrigerao ar condicionado Refrigerao freezer Refrigerao ar Refrigerao climatizador Refrigerao
  
      PETS E AGRO 
    pet Pet Shop racao Pet Shop cachorro Pet Shop gato Pet Shop banho e tosa Pet Shop veterinario Pet Shop viva Pet Shop aquario Pet Shop

      MANUTENO REFORMA E CONSTRUO 
    vazamento Encanador cano Encanador torneira Encanador desentupir Encanador caixa dagua Encanador esgoto Encanador hidraulica Encanador
    curto Eletricista fiacao Eletricista luz Eletricista chuveiro Eletricista tomada Eletricista disjuntor Eletricista energia Eletricista fio Eletricista
    pintar Pintor pintura Pintor parede Pintor massa corrida Pintor verniz Pintor
    reforma Pedreiro piso Pedreiro azulejo Pedreiro obra Pedreiro tijolo Pedreiro cimento Pedreiro reboco Pedreiro alicerce Pedreiro
    gesso Gesseiro drywall Gesseiro sanca Gesseiro forro Gesseiro
    telhado Telhadista goteira Telhadista calha Telhadista
    solda Serralheiro portao Serralheiro grade Serralheiro aluminio Serralheiro ferro Serralheiro
    vidro Vidraceiro janela Vidraceiro box Vidraceiro espelho Vidraceiro
    chave Chaveiro fechadura Chaveiro tranca Chaveiro copia Chaveiro abertura Chaveiro

      AUTOMOTIVO 
    carro Mecnico motor Mecnico oficina Mecnico freio Mecnico suspensao Mecnico cambio Mecnico
    pneu Borracheiro estepe Borracheiro furou Borracheiro vulcanizacao Borracheiro balanceamento Borracheiro
    guincho Guincho 24h reboque Guincho 24h plataforma Guincho 24h
    lavajato Esttica Automotiva lavagem Esttica Automotiva polimento Esttica Automotiva limpeza de banco Esttica Automotiva

      LOGSTICA E SERVIOS GERAIS 
    frete Freteiro mudanca Freteiro carreto Freteiro transporte Freteiro
    montar Montador armario Montador moveis Montador guarda roupa Montador cozinha Montador
    faxina Diarista limpeza Diarista passar Diarista arrumadeira Diarista
    jardim Jardineiro grama Jardineiro poda Jardineiro rocar Jardineiro
    piscina Piscineiro cloro Piscineiro limpeza de piscina Piscineiro
    ajudante Ajudante Geral braco Ajudante Geral carga Ajudante Geral


 
 4 MOTORES DE IA E GEOLOCALIZAO
 
def normalizarparaiatexto
    if not texto return 
    return joinc for c in unicodedatanormalizeNFD strtexto 
                  if unicodedatacategoryc  Mnlowerstrip

def processariaavancadatexto
    if not texto return Vazio
    tclean  normalizarparaiatexto
    
     1 Busca exata no dicionrio de conceitos Pizzaria Mecnico etc
    for chave categoria in CONCEITOSEXPANDIDOSitems
        chavenorm  normalizarparaiachave
        if researchrfbchavenormb tclean
            return categoria
            
     2 Verifica se o usurio digitou exatamente uma categoria oficial
    for cat in CATEGORIASOFICIAIS
        if normalizarparaiacat in tclean
            return cat
            
     3 MUDANA AQUI Se no encontrar NADA retorna um termo que force o vazio
     Isso far com que o app mostre sua frase de compartilhamento
    return NAOENCONTRADO

def calculardistanciareallat1 lon1 lat2 lon2
    try
        if None in lat1 lon1 lat2 lon2 return 9990
        R  6371 
        dlat dlon  mathradianslat2  lat1 mathradianslon2  lon1
        a  mathsindlat22  mathcosmathradianslat1  mathcosmathradianslat2  mathsindlon22
        return roundR  2  mathatan2mathsqrta mathsqrt1a 1
    except return 9990

def converterimgb64file
    if file is None return 
    try return base64b64encodefilereaddecode
    except return 
def enviaralertaadminnomeprof categoriaprof whatsappprof
    
    Gera um link de notificao para o Admin 
    Nota Para automao 100 invisvel seria necessria uma API paga como Twilio ou ZAPI
    Esta verso gera um log e um alerta visual imediato no painel
    
    msgalerta  f NOVO CADASTRO NO GERALJnn 
                 f Nome nomeprofn 
                 f rea categoriaprofn 
                 f Zap whatsappprofnn 
                 fAcesse o Painel Admin para aprovar
    
     Codifica a mensagem para URL
    msgencoded  msgalertareplacen 0Areplace  20
    linkzapadmin  fhttpswameZAPADMINtextmsgencoded
    
    return linkzapadmin
 
 SISTEMA GUARDIAO  IA DE AUTORRECUPERAO E SEGURANA
 

def guardiaescanearecorrigir
    Varre o banco de dados em busca de erros de estrutura e corrige na hora
    statuslog  
    try
        profs  dbcollectionprofissionaisstream
        for pdoc in profs
            dados  pdoctodict
            idpro  pdocid
            correcoes  

             1 Verifica campos nulos que causam travamentos
            if not dadosgetarea or dadosgetarea not in CATEGORIASOFICIAIS
                correcoesarea  Ajudante Geral
            
            if not dadosgetdescricao
                correcoesdescricao  Profissional parceiro do ecossistema GeralJ Brasil
            
            if dadosgetsaldo is None
                correcoessaldo  0
            
            if dadosgetlat is None or dadosgetlon is None
                correcoeslat  LATREF
                correcoeslon  LONREF

             2 Se houver algo errado aplica a cura automtica
            if correcoes
                dbcollectionprofissionaisdocumentidproupdatecorrecoes
                statuslogappendf Corrigido idpro
        
        return statuslog if statuslog else SISTEMA NTEGRO Nenhum erro encontrado
    except Exception as e
        return f Erro no Scanner e

def scanvirusescripts
    Detecta se h tentativas de injeo de scripts maliciosos nos campos de texto
    alertas  
    profs  dbcollectionprofissionaisstream
     Padres comuns de ataque XSS e Injeo
    padroesperigosos  rscript rjavascript rDROP TABLE rOR 11
    
    for pdoc in profs
        dados  pdoctodict
        conteudo  strdadosgetnome   strdadosgetdescricao 
        
        for padrao in padroesperigosos
            if researchpadrao conteudo reIGNORECASE
                alertasappendf PERIGO Contedo suspeito no ID pdocid
                 Bloqueia o profissional preventivamente
                dbcollectionprofissionaisdocumentpdocidupdateaprovado False
    
    return alertas if alertas else LIMPO Nenhum script malicioso detectado
 
 5 DESIGN SYSTEM
 
stmarkdown
style
    import urlhttpsfontsgoogleapiscomcss2familyInterwght400700900displayswap
      fontfamily Inter sansserif 
    stApp  backgroundcolor F8FAFC 
    headercontainer  background white padding 40px 20px borderradius 0 0 50px 50px textalign center boxshadow 0 10px 30px rgba000005 borderbottom 8px solid FF8C00 marginbottom 25px 
    logoazul  color 0047AB fontweight 900 fontsize 50px letterspacing 2px 
    logolaranja  color FF8C00 fontweight 900 fontsize 50px letterspacing 2px 
    procard  background white borderradius 25px padding 25px marginbottom 20px borderleft 15px solid 0047AB boxshadow 0 10px 20px rgba000004 display flex alignitems center 
    proimg  width 100px height 100px borderradius 50 objectfit cover marginright 25px border 4px solid F1F5F9 
    btnzap  background 22C55E color white important padding 15px borderradius 15px textdecoration none fontweight 800 display block textalign center margintop 10px 
    metricbox  background 1E293B color white padding 20px borderradius 20px textalign center borderbottom 4px solid FF8C00 
style
 unsafeallowhtmlTrue

stmarkdowndiv classheadercontainerspan classlogoazulGERALspanspan classlogolaranjaJspanbrsmall stylecolor64748B fontweight700BRASIL ELITE EDITIONsmalldiv unsafeallowhtmlTrue

 1 Defina a lista bsica
listaabas   BUSCAR  CADASTRAR  MEU PERFIL  ADMIN  FEEDBACK

 2 Verifique o comando secreto na barra lateral
comando  stsidebartextinputComando Secreto typepassword

 3 Se o comando estiver certo soma a aba financeira
if comando  abracadabra
    listaabasappend FINANCEIRO

 4 Cria as abas no Streamlit
menuabas  sttabslistaabas

  ABA 1 BUSCA SISTEMA GPS  RANKING ELITE  VITRINE 
with menuabas0
    stmarkdown  O que voc precisa
    
      MOTOR DE LOCALIZAO EM TEMPO REAL 
    with stexpander Sua Localizao GPS expandedFalse
        loc  getgeolocation
        if loc
            minhalat  loccoordslatitude
            minhalon  loccoordslongitude
            stsuccessfLocalizao detectada
        else
            minhalat  LATREF
            minhalon  LONREF
            stwarningGPS desativado Usando localizao padro SP

    c1 c2  stcolumns3 1
    termobusca  c1textinputEx Cano estourado ou Pizza keymainsearch
    raiokm  c2selectsliderRaio KM options1 3 5 10 20 50 100 500 2000 value10
    
    if termobusca
         Processamento via IA para identificar a categoria
        catia  processariaavancadatermobusca
        stinfof IA Buscando por catia prximo a voc
        
         Lgica de Horrio em tempo real
        from datetime import datetime
        import pytz
        import re
        from urllibparse import quote
        
        fuso  pytztimezoneAmericaSaoPaulo
        horaatual  datetimenowfusostrftimeHM

         Busca no Firebase Filtra apenas aprovados e da categoria certa
        profs  dbcollectionprofissionaiswherearea  catiawhereaprovado  Truestream
        
        listaranking  
        for pdoc in profs
            p  pdoctodict
            pid  pdocid
            
             CALCULA DISTNCIA REAL GPS vs Profissional
            dist  calculardistanciarealminhalat minhalon pgetlat LATREF pgetlon LONREF
            
            if dist  raiokm
                pdist  dist
                 MOTOR DE SCORE ELITE Ranking
                score  0
                score  500 if pgetverificado False else 0
                score  pgetsaldo 0  10
                score  pgetrating 5  20
                pscoreelite  score
                listarankingappendp

         Ordenao Elite primeiro maior score depois os mais prximos menor distncia
        listarankingsortkeylambda x xscoreelite xdist

        if not listaranking
            stmarkdownf
            div stylebackgroundcolor FFF4E5 padding 20px borderradius 15px borderleft 5px solid FF8C00
                h3 stylecolor 856404 Essa profisso ainda no foi preenchida nesta regioh3
                p stylecolor 856404Compartilhe o bGeralJb e ajude a crescer sua rede localp
            div
             unsafeallowhtmlTrue
            
            linkshare  httpswametextEi20Procurei20um20servio20no20GeralJ20e20vi20que20ainda20temos20vagas20Cadastrese20httpsgeraljastreamlitapp
            stmarkdownfa hreflinkshare targetblank styletextdecorationnonediv stylebackground22C55E colorwhite padding15px borderradius10px textaligncenter fontweightbold margintop10px COMPARTILHAR NO WHATSAPPdiva unsafeallowhtmlTrue
        
        else
              RENDERIZAO DOS CARDS LOOP 
            for p in listaranking
                pid  pid
                iselite  pgetverificado and pgetsaldo 0  0
                
                with stcontainer
                     Cores dinmicas baseadas no tipo de conta
                    corborda  FFD700 if iselite else FF8C00 if pgettipo   ComrcioLoja else 0047AB
                    bgcard  FFFDF5 if iselite else FFFFFF
                    
                    stmarkdownf
                    div styleborderleft 8px solid corborda padding 15px background bgcard borderradius 15px marginbottom 5px boxshadow 0 4px 6px rgba000005
                        span stylefontsize 12px color gray fontweight bold a pdist1f km de voc    DESTAQUE if iselite else span
                    div
                     unsafeallowhtmlTrue

                    colimg coltxt  stcolumns1 4
                    with colimg
                        foto  pgetfotourl httpsviaplaceholdercom150
                        stmarkdownfimg srcfoto stylewidth75px height75px borderradius50 objectfitcover border3px solid corborda unsafeallowhtmlTrue
                    
                    with coltxt
                        nomeexibicao  pgetnome upper
                        if pgetverificado False nomeexibicao   span stylecolor1DA1F2span
                        
                        statusloja  
                        if pgettipo   ComrcioLoja
                            hab hfe  pgethabre 0800 pgethfecha 1800
                            statusloja    b stylecolorgreenABERTOb if hab  horaatual  hfe else   b stylecolorredFECHADOb
                        
                        stmarkdownfnomeexibicao statusloja unsafeallowhtmlTrue
                        stcaptionfpgetdescricao 120

                     Vitrine de Fotos do Portflio
                    if pgetportfolioimgs
                        colsv  stcolumns3
                        for i imgb64 in enumeratepgetportfolioimgs3
                            colsviimageimgb64 usecontainerwidthTrue

                      LGICA DO BOTO DE WHATSAPP AQUI DENTRO DO LOOP 
                    nomecurto  pgetnome Profissionalsplit0upper
                    
                     Limpeza do nmero de telefone ID do documento
                    numerolimpo  resubrD  strpid
                    if not numerolimpostartswith55
                        numerolimpo  f55numerolimpo
                    
                    textozap  quotefOl pgetnome vi seu perfil no GeralJ
                    linkfinal  fhttpswamenumerolimpotexttextozap

                      BOTO NICO VISUAL TOP  ABRE SEMPRE 
                    import re
                    from urllibparse import quote
                    
                     1 Preparao dos dados
                    numlimpo  resubrD  strpid
                    if not numlimpostartswith55 numlimpo  f55numlimpo
                    textozap  quotefOl pgetnome vi seu perfil no GeralJ
                    linkfinal  fhttpswamenumlimpotexttextozap
                    nomebtn  pgetnome Profissionalsplit0upper
                    
                     2 BOTO HTML Ocupa o lugar do stbutton
                     Este boto abre o WhatsApp instantaneamente e no  bloqueado
                    stmarkdownf
                        a hreflinkfinal targetblank styletextdecoration none
                            div style
                                backgroundcolor 25D366
                                color white
                                padding 15px
                                borderradius 12px
                                textalign center
                                fontweight bold
                                fontsize 18px
                                boxshadow 0 4px 8px rgba000015
                                transition 03s
                                cursor pointer
                                margintop 10px
                            
                                 FALAR COM nomebtn
                            div
                        a
                     unsafeallowhtmlTrue
                    
                     3 LGICA DE DBITO E SEGURANA
                 Verifica se tem saldo antes de processar
                if pgetsaldo 0  0
                    continue    AGORA EST DENTRO DO IF 4 espaos

                 Se passou pelo if acima registra o cliquevisualizao
                dbcollectionprofissionaisdocumentpidupdate
                    cliques pgetcliques 0  1
                
  ABA 2 PAINEL DO PARCEIRO VERSO COM TEMA MANUAL 
with menuabas2
    if auth not in stsessionstate stsessionstateauth  False
    
    if not stsessionstateauth
        stsubheader Acesso ao Painel
        col1 col2  stcolumns2
        lzap  col1textinputWhatsApp nmeros keyloginzapv7
        lpw  col2textinputSenha typepassword keyloginpwv7
        
        if stbuttonENTRAR NO PAINEL usecontainerwidthTrue keybtnentrarv7
            u  dbcollectionprofissionaisdocumentlzapget
            if uexists and utodictgetsenha  lpw
                stsessionstateauth stsessionstateuserid  True lzap
                strerun
            else sterrorDados incorretos
    else
        docref  dbcollectionprofissionaisdocumentstsessionstateuserid
        d  docrefgettodict
        
         1 MTRICAS Usando colunas nativas para evitar conflito de CSS
        stwritef Ol dgetnome Parceiro
        m1 m2 m3  stcolumns3
        m1metricSaldo  fdgetsaldo 0
        m2metricCliques  fdgetcliques 0
        m3metricStatus  ATIVO if dgetaprovado else  PENDENTE

         2 GPS Funo preservada
        if stbutton ATUALIZAR LOCALIZAO GPS usecontainerwidthTrue keygpsv7
            loc  streamlitjsevaljsexpressionsnavigatorgeolocationgetCurrentPositions  s keygpsv7eval
            if loc and coords in loc
                docrefupdatelat loccoordslatitude lon loccoordslongitude
                stsuccess Localizao salva
            else stinfoAguardando sinal Clique novamente

        stdivider

         3 COMPRA DE MOEDAS PIX  Variveis oficiais preservadas
        with stexpander COMPRAR MOEDAS PIX expandedFalse
            stwarningfChave PIX PIXOFICIAL
            c1 c2 c3  stcolumns3
            if c1button10 Moedas keyp10v7 stcodePIXOFICIAL
            if c2button50 Moedas keyp50v7 stcodePIXOFICIAL
            if c3button100 Moedas keyp100v7 stcodePIXOFICIAL
            
            stlinkbutton ENVIAR COMPROVANTE AGORA fhttpswameZAPADMINtextFiz o PIX stsessionstateuserid usecontainerwidthTrue

         4 EDIO DE PERFIL FOTOS HORRIOS E SEGMENTO
        with stexpander EDITAR MEU PERFIL  VITRINE expandedTrue
            with stformperfilv7
                nnome  sttextinputNome Profissional dgetnome 
                
                  VOLTANDO A FUNO DE MUDAR SEGMENTO 
                 Procura a categoria atual na lista para deixar selecionada
                try
                    indexcat  CATEGORIASOFICIAISindexdgetarea Ajudante Geral
                except
                    indexcat  0
                narea  stselectboxMudar meu Segmentorea CATEGORIASOFICIAIS indexindexcat
                 

                ndesc  sttextareaDescrio dgetdescricao 
                ncat  sttextinputLink CatlogoInstagram dgetlinkcatalogo 
                
                h1 h2  stcolumns2
                nabre  h1textinputAbre s ex 0800 dgethabre 0800
                nfecha  h2textinputFecha s ex 1800 dgethfecha 1800
                
                nfoto  stfileuploaderTrocar Foto Perfil typejpgpngjpeg keyfv7
                nportfolio  stfileuploaderVitrine At 3 fotos typejpgpngjpeg acceptmultiplefilesTrue keypv7
                
                if stformsubmitbuttonSALVAR ALTERAES usecontainerwidthTrue
                     Adicionei area no dicionrio de update
                    up  
                        nome nnome 
                        area narea   Agora ele salva a nova categoria
                        descricao ndesc 
                        linkcatalogo ncat 
                        habre nabre 
                        hfecha nfecha
                    
                    
                    if nfoto 
                        upfotourl  fdataimagepngbase64converterimgb64nfoto
                    
                    if nportfolio
                        upportfolioimgs  fdataimagepngbase64converterimgb64f for f in nportfolio3
                    
                    docrefupdateup
                    stsuccess Perfil e Segmento atualizados com sucesso
                    timesleep1  Pequena pausa para o usurio ver a mensagem
                    strerun
  ABA 1 CADASTRAR SISTEMA DE ADMISSO DE ELITE 
with menuabas1
    stmarkdown  Cadastro de Profissional
    stinfoPreencha os dados abaixo para entrar no ecossistema GeralJ

     Incio do Formulrio  O with garante que tudo aqui dentro pertena ao boto de salvar
    with stformformnovoprofissional clearonsubmitFalse
        colid1 colid2  stcolumns2
        nomeinput  colid1textinputNome do Profissional ou Loja placeholderEx Joo Mecnico
        zapinput  colid2textinputWhatsApp DDD  Nmero placeholderEx 11991853488
        
        colid3 colid4  stcolumns2
        categoriainput  colid3selectboxSua rea Principal CATEGORIASOFICIAIS
        senhainput  colid4textinputCrie uma Senha typepassword helpPara editar seu perfil depois
        
        descricaoinput  sttextareaDescrio do Servio placeholderConte o que voc faz diferenciais e experincia
        
        tipoinput  stradioTipo de Cadastro  Profissional Autnomo  ComrcioLoja horizontalTrue
        
        fotoupload  stfileuploaderFoto de Perfil ou Logo typejpg jpeg png

        stmarkdown
        stcaption A sua localizao atual ser capturada automaticamente para te mostrar nos resultados prximos aos clientes
        
         O BOTO DE SALVAR PRECISA ESTAR AQUI DENTRO DO FORM
        btnfinalizar  stformsubmitbutton FINALIZAR E SALVAR CADASTRO usecontainerwidthTrue

     Lgica que acontece APS o clique no boto
    if btnfinalizar
        if not nomeinput or not zapinput or not senhainput
            sterror ERRO Nome WhatsApp e Senha so obrigatrios
        else
            with stspinnerConectando ao banco de dados
                try
                     1 Processamento da Imagem
                    fotofinal  
                    if fotoupload
                        fotofinal  fdataimagepngbase64converterimgb64fotoupload
                    
                     2 Garantia de Localizao Se o GPS falhar usa a LATREFLONREF que voc definiu
                     Use as variveis que o seu script j detectou no topo da pgina
                    latsalvar  minhalat if minhalat in locals else LATREF
                    lonsalvar  minhalon if minhalon in locals else LONREF

                     3 Montagem do Objeto Sem apagar nada do que voc j usa
                    novopro  
                        nome nomeinput
                        area categoriainput
                        descricao descricaoinput
                        senha senhainput
                        tipo tipoinput
                        whatsapp zapinput
                        fotourl fotofinal
                        saldo BONUSWELCOME  D os 5 crditos iniciais
                        aprovado True         J nasce ativo conforme seu fluxo
                        verificado False
                        cliques 0
                        rating 5
                        lat latsalvar
                        lon lonsalvar
                        datacadastro datetimedatetimenowstrftimedmY
                    

                     4 Envio para o Firestore usando o WhatsApp como ID Evita duplicados
                    dbcollectionprofissionaisdocumentzapinputsetnovopro
                    
                    stballoons
                    stsuccessf BEMVINDO nomeinputupper Seu cadastro foi concludo com sucesso
                    stinfo DICA V na aba  MEU PERFIL para fazer login e ver seu saldo de moedas
                    
                     Alerta para o Admin Usando sua funo existente
                    linkadmin  enviaralertaadminnomeinput categoriainput zapinput
                    stmarkdownf Avisar Administrao via WhatsApplinkadmin

                except Exception as e
                    sterrorf Erro tcnico ao salvar e
with menuabas3
    stmarkdown  Terminal de Administrao
    accessadm  sttextinputSenha Master typepassword keyadmauthfinal
    
     BLOQUEIO DE SEGURANA REFORADO
    if accessadm  CHAVEADMIN
        if accessadm  
            sterror Acesso negado Senha incorreta
        else
            stinfoAguardando chave master para liberar sistemas
        ststop 

      DAQUI PARA BAIXO TUDO EST PROTEGIDO PELA SENHA 
    stsuccess Acesso Autorizado Bemvindo ao Painel Supremo
    
     1 BUSCA DE DADOS E TELEMETRIA
    allprofslista  listdbcollectionprofissionaisstream
    totalcadastros  lenallprofslista
    pendenteslista  p for p in allprofslista if not ptodictgetaprovado False
    totalmoedas  sumptodictgetsaldo 0 for p in allprofslista
    totalcliques  sumptodictgetcliques 0 for p in allprofslista

     Painel de Indicadores
    c1 c2 c3 c4  stcolumns4
    c1metric Moedas ftotalmoedas 
    c2metric Parceiros totalcadastros
    c3metric Cliques totalcliques
    c4metric Pendentes lenpendenteslista deltacolorinverse
    
    stdivider

     2 ABAS DE COMANDO INTERNAS
    tgestao taprova tseguranca tfeed  sttabs
         GESTO DE ATIVOS  NOVOS APROVAO  SEGURANA IA  FEEDBACKS
    

      ABA INTERNA GESTO DE ATIVOS BUSCA E EDIO 
    with tgestao
        searchpro  sttextinput Buscar parceiro por Nome ou WhatsApp placeholderEx Joo ou 11999
        for pdoc in allprofslista
            p pid  pdoctodict pdocid
             Filtro de Busca
            if not searchpro or searchprolower in pgetnome lower or searchpro in pid
                statuscor   if pgetaprovado else 
                with stexpanderfstatuscor pgetnome Sem Nomeupper  pgetarea
                    cola colb  stcolumns2
                    with cola
                        stwritefWhatsAppID pid
                        stwritefSaldo Atual pgetsaldo 0 moedas
                        
                         Controle de Verificado Selo
                        isverif  pgetverificado False
                        if sttoggleSelo Verificado valueisverif keyftglpid
                            if not isverif dbcollectionprofissionaisdocumentpidupdateverificado True strerun
                        else
                            if isverif dbcollectionprofissionaisdocumentpidupdateverificado False strerun
                    
                    with colb
                         Adicionar Moedas
                        bonus  stnumberinputAdicionar Moedas value0 keyfnumpid
                        if stbutton CREDITAR keyfcbtnpid usecontainerwidthTrue
                            dbcollectionprofissionaisdocumentpidupdatesaldo pgetsaldo 0  bonus
                            stsuccessCreditado timesleep05 strerun
                        
                        if stbutton BANIRREMOVER keyfdelpid usecontainerwidthTrue
                            dbcollectionprofissionaisdocumentpiddelete
                            sterrorRemovido timesleep05 strerun

      ABA INTERNA FILA DE APROVAO 
    with taprova
        if not pendenteslista
            stinfoNenhum cadastro pendente
        else
            for pdoc in pendenteslista
                p pid  pdoctodict pdocid
                stwarningfSOLICITAO pgetnome pgetarea
                if stbuttonf APROVAR pgetnomeupper keyfokpid
                    dbcollectionprofissionaisdocumentpidupdateaprovado True saldo 10
                    stsuccessAprovado com bnus timesleep05 strerun

      ABA INTERNA SEGURANA IA 
    with tseguranca
        stmarkdown  Central de Proteo e AutoCura
        scol1 scol2  stcolumns2
        if scol1button ESCANEAR AMEAAS usecontainerwidthTrue
            alertas  scanvirusescripts
            for a in alertas stwritea
            
        if scol2button REPARAR BANCO usecontainerwidthTrue
            reparos  guardiaescanearecorrigir
            for r in reparos stwriter
            stballoons

  ABA INTERNA FEEDBACKS DENTRO DA CENTRAL DE COMANDO 
    with tfeed
        try
            feedbacks  listdbcollectionfeedbacksorderbydata directionDESCENDINGlimit20stream
            if feedbacks
                for f in feedbacks
                    df  ftodict
                    
                     CORREO DO ERRO Converte para string antes de cortar os 10 caracteres
                    databruta  dfgetdata Sem data
                    datatxt  strdatabruta10 
                    
                    nota  dfgetnota SN
                    msg  dfgetmensagem 
                    
                    stmarkdownf
                        div stylebackgroundcolor f0f2f6 padding 10px borderradius 10px marginbottom 10px borderleft 5px solid 0047AB
                            small datatxtsmallbr
                            b notabbr
                            p stylemargin0msgp
                        div
                     unsafeallowhtmlTrue
            else
                stinfoNenhuma nova mensagem na caixa de entrada
        except Exception as e
            sterrorfErro ao carregar mensagens e

    stdivider
    stcaptionO GeralJ utiliza os seus feedbacks para melhorar a segurana e a qualidade dos prestadores de servio
  ABA 6 FINANCEIRO S APARECE SOB COMANDO 
 Este if evita o IndexError ele s executa se a aba financeira existir
if lenmenuabas  5
    with menuabas4
        stmarkdown  Gesto de Capital GeralJ
        
         Chave de segurana extra para abrir o cofre
        senhacofre  sttextinputChave do Cofre typepassword keycofrevFinal
        
        if senhacofre  riqueza2025
            allp  listdbcollectionprofissionaisstream
            vendas  sumptodictgettotalcomprado 0 for p in allp
            
            c1 c2  stcolumns2
            c1metric FATURAMENTO REAL fR vendas2f
            c2metric TOTAL PARCEIROS lenallp
            
            stdivider
             Tabela de conferncia
            stwriteHistrico de Vendas
            tabela  Profissional ptodictgetnome Total Pago ptodictgettotalcomprado 0 for p in allp
            stdataframetabela usecontainerwidthTrue
        else
            stinfoAguardando chave mestra para exibir dados sensveis
              ABA FEEDBACK A VOZ DO CLIENTE 
with menuabas4  Verifique se o ndice da sua aba de feedback  4 ou 5
    stmarkdown  Sua opinio  fundamental
    stwriteContenos como foi a sua experincia com o GeralJ
    
    with stformfeedbackform clearonsubmitTrue
        nota  stselectslider
            Qual a sua satisfao geral
            optionsMuito Insatisfeito Insatisfeito Regular Satisfeito Muito Satisfeito
            valueMuito Satisfeito
        
        
        comentario  sttextarea
            Descreva a sua experincia ou deixe uma sugesto
            placeholderEx O profissional foi muito atencioso
            height150
        
        
        btnenviar  stformsubmitbuttonENVIAR AVALIAO usecontainerwidthTrue
        
        if btnenviar
            if comentariostrip  
                try
                     Salvando com data formatada para evitar erros de leitura
                    agora  datetimedatetimenow
                    datastring  agorastrftimeYmd HMS
                    
                    dbcollectionfeedbacksadd
                        data datastring  Salva como texto padro
                        nota nota
                        mensagem comentario
                        lido False
                    
                    stsuccess Muito obrigado Sua mensagem foi enviada
                    stballoons
                except Exception as e
                    sterrorfErro ao enviar e
            else
                stwarning Por favor escreva algo antes de enviar
                
 
 RODAP NICO Final do Arquivo
 
  RODAP CORRIGIDO 
try
    anoatual  datetimedatetimenowyear
except
    anoatual  2025  Valor padro caso o mdulo falhe

stmarkdownfdiv styletextaligncenter padding20px color94A3B8 fontsize10pxGERALJ v200  anoatualdiv unsafeallowhtmlTrue

















