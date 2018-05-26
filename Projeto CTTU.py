
# coding: utf-8

# In[1]:


import pandas
import geopandas
from shapely.geometry import Point
import numpy
import re
import holoviews


# In[2]:


holoviews.notebook_extension('bokeh')


# Eu utilizei somente os datasets que possuem dados de latitude e longitude inicialmente mas a ideia
# é adicionar informações de bairro.

# # Data Sources
# 
# As fontes de dados são do site dados.recife.pe.gov.br. Todas são relacionadas à CTTU

# In[3]:


acidentes_2014 = pandas.read_csv("data/acidentes-2014.csv", sep=";")
acidentes_2015 = pandas.read_csv("data/acidentes-2015.csv", sep=";")
acidentes_2016 = pandas.read_csv("data/acidentes-2016.csv", sep=";")


# In[4]:


equipamentos_monitoramento = pandas.read_csv("data/equipamentos-de-monitoramento-e-ficalizacao.csv", sep=";")


# In[5]:


semaforos = pandas.read_csv("data/semaforos.csv", sep=";")


# In[6]:


fiscalizacao = pandas.read_csv("data/fiscalizacao-eletronica.csv", sep=";")


# In[7]:


monitoramento = pandas.read_csv("data/monitoramentocttu.csv", sep=";")


# In[8]:


infracoes_2014 = pandas.read_csv("data/infracoes/relatorio-de-multas-implantadas-em-2014.csv", sep=";")
infracoes_2015 = pandas.read_csv("data/infracoes/relatorio-de-multas-implantadas-em-2015.csv", sep=";")
infracoes_2016 = pandas.read_csv("data/infracoes/relatorio-de-multas-implantadas-em-2016.csv", sep=";")


# 
# ## Discussão
# Um desafio significante do projeto foi juntar os dataframes a partir dos lat e longs, como juntar exemplos, 
# como calcular a distância ótima para que acidentes não fossem inseridos próximos de dois semafóros, por exempo?
# 
# 

# # Exploração - Infrações

# In[9]:


infracoes_2014.columns


# In[91]:


infracoes_2015.columns


# In[92]:


infracoes_2016.columns


# # Exploração - fiscalização

# In[13]:


fiscalizacao.head(10)


# In[14]:


fiscalizacao.dtypes


# In[15]:


fiscalizacao.shape


# In[16]:


fiscalizacao.describe()


# # Exploração - Semaforos

# In[17]:


semaforos.describe()


# In[18]:


semaforos.shape


# In[19]:


semaforos.head(20)


# # Data Cleaning

# ## Infrações

# Extrair a informação dos semáforos onde aconteceram as infrações, utilizando essa informação, vou ser
# capaz de mergear as infrações com os semaforos e suas localizações.

# In[12]:


infracoes_2014["numero_semaforo"] = infracoes_2014["localcometimento"].str.extract("[N|N.]{1}\s?([0-9]{1,4})")
infracoes_2015["numero_semaforo"] = infracoes_2015["localcometimento"].str.extract("[N|N.]{1}\s?([0-9]{1,4})")
infracoes_2016["numero_semaforo"] = infracoes_2016["localcometimento"].str.extract("[N|N.]{1}\s?([0-9]{1,4})")


# Como é possível perceber abaixo, o formato das datas estão em formatos diferentes entre os anos de 2014
# e 2015-2016. Tenho de arrumar isto também.

# In[13]:


infracoes_2014.head(5)


# In[14]:


infracoes_2015.head(5)


# In[15]:


infracoes = [infracoes_2014, infracoes_2015, infracoes_2016]
infracoes_2014_2016 = pandas.concat(infracoes)


# In[16]:


infracoes_2014_2016.head(10)


# In[18]:


date_columns = ["datainfracao", "horainfracao", "dataimplantacao"]
for column in date_columns:
    infracoes_2014_2016[column] = pandas.to_datetime(infracoes_2014_2016[column])


# ## Monitoramento

# In[22]:


monitoramento['geometry'] = monitoramento.apply(lambda example: Point(example.longitude, example.latitude), axis=1)


# In[23]:


monitoramento = geopandas.GeoDataFrame(monitoramento)
monitoramento.head(5)


# Não achei necessário a transformação de nenhum tipo do dataset de monitoramento, apenas a transformação
# do tipo para **GeoDataFrame** e a criação da coluna location

# ## Fiscalizacao

# In[25]:


fiscalizacao["geometry"] = fiscalizacao.apply(lambda example: Point(example.LONGITUDE, example.LATITUDE), axis=1)


# In[26]:


fiscalizacao = geopandas.GeoDataFrame(fiscalizacao)


# ## Semáforos

# In[30]:


semaforos["geometry"] = semaforos.apply(lambda example: Point(example.Longitude, example.Latitude), axis=1)


# In[31]:


semaforos = geopandas.GeoDataFrame(semaforos)


# In[37]:


categorical_columns = ["funcionamento", "sinalsonoro", "sinalizadorciclista"]
for column in categorical_columns:
    semaforos[column] = semaforos[column].astype('category')


# In[41]:


semaforos["funcionamento"] = semaforos["funcionamento"].replace({'E/GIt': "E/Git", "E/GIT": "E/Git"})


# In[46]:


semaforos.dropna(subset=["Longitude"], inplace=True)


# Mesmo que os valores Veicular e Pedestre não estejam presentes no dicionário de dados, não 
# há indicação para o descarte, então irei mantê-los

# ## Acidentes

# Todos os dados que não são números considerei como "0", dado que não há informação na internet ou no 
# dicionário de dados acerca dos seus significados.

# In[52]:


# regex to transform 2014 dates
import re
pattern = "([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})"
regex = re.compile(pattern)
#test code
"""test = "3/1/2014"

match = regex.search(test)

print(match.group(1))
for group in match.groups():
    print(group)"""


# In[53]:


date_format = "{0}/{1}/{2}"
def transformDate(month, day, year):
    if len(day) == 1:
        day = "0"+day
    if len(month) == 1:
        month = "0"+month
    return date_format.format(day, month, year)


# In[54]:


match_lambda = lambda match: transformDate(match.group(1), 
                                           match.group(2), 
                                           match.group(3))


# In[55]:


acidentes_2014["data"] = acidentes_2014["data"].apply(lambda data: match_lambda(regex.search(data)))


# Como é possível perceber, as datas de 2015 e 2016 são do tipo %d/%m/%y contudo as de 2014 são %m/%d/%y
# e o mês e dia não possuem o zero na frente, vou ter de modificar a ordem e esta falta de 0.

# Percebi que a coluna tipo do dataset de 2014 é o mesmo tipo_de_ocorrencia de 2015 e 2016, então  a 
# renomiei para "tipo de ocorrencia"

# In[61]:


map_2015_2016 = {"data_abertura": "data de abertura", "hora_abertura": "hora de abertura",
                "quantidade_vitimas": "quantidade de vitimas", "tipo_ocorrencia": "tipo de ocorrencia"}


# In[62]:


map_2014_2016 = {"tipo": "tipo de ocorrencia"}


# In[63]:


acidentes_2014 = acidentes_2014.rename(map_2014_2016, axis='columns')
acidentes_2014.columns


# In[64]:


acidentes_2015 = acidentes_2015.rename(map_2015_2016, axis='columns')
acidentes_2015.columns


# In[68]:


acidentes_2014_2016 = pandas.concat([acidentes_2014, acidentes_2015, acidentes_2016])


# In[71]:


changed_values = {"F" : 0, "f": 0, "'''": 0, "VT": 0, "-": 0, " ": 0}
acidentes_2014_2016["quantidade de vitimas"] = acidentes_2014_2016["quantidade de vitimas"].replace(changed_values)


# In[72]:


acidentes_2014_2016["quantidade de vitimas"] = acidentes_2014_2016["quantidade de vitimas"].fillna(0)


# In[75]:


acidentes_2014_2016["quantidade de vitimas"] = acidentes_2014_2016["quantidade de vitimas"].astype('int')


# In[76]:


acidentes_2014_2016.bairro = acidentes_2014_2016.bairro.astype('category')


# No dicionário de dados não há nada que mencione se há uma diferença entre "Moto e Ciclomotor" e "Motos e Ciclomotores", 
# irei assumir que não há, dado que no máximo o que haverá será uma diferença na quantidade, se houver, 
# acho que a perda de informação será mínima. 
# 
# Colocarei Motocicletas em separado pois acho que são uma categoria diferente de ciclomotor (como mostrado, há uma categoria "Ciclomotores"

# In[82]:


default_colisao_cicl_pedestrians_value = "Ciclistas e Pedestre"
acidentes_2014_2016["tipo de ocorrencia"] = acidentes_2014_2016["tipo de ocorrencia"].replace({"Ciclistas e pedestre": default_colisao_cicl_pedestrians_value, 
                                                  "Pedestres e ciclista": default_colisao_cicl_pedestrians_value})


# In[83]:


default_colisao = "Colisão"
acidentes_2014_2016["tipo de ocorrencia"] = acidentes_2014_2016["tipo de ocorrencia"].replace({"COLISÃO": default_colisao,
                                                                                              '"COLISÃO': default_colisao,
                                                                                              'Colisoes': default_colisao,
                                                                                              'COLISÃOa': default_colisao,
                                                                                              "COLISÃO\t2016 13 050\t": default_colisao,
                                                                                              "COLISÃO": default_colisao})


# In[84]:


default_atropelamento = "Atropelamento"
acidentes_2014_2016["tipo de ocorrencia"] = acidentes_2014_2016["tipo de ocorrencia"].replace({
    "ATROPELAMENTOa": default_atropelamento,
    "ATROPELAMENTO": default_atropelamento,
    "Atropelamentos": default_atropelamento,
    
})


# In[85]:


default_acid_percurso = "ACID. DE PERCURSO"
acidentes_2014_2016["tipo de ocorrencia"] = acidentes_2014_2016["tipo de ocorrencia"].replace({
    "ACID DE PERCURSO": default_acid_percurso
})


# In[86]:


default_moto_ciclomotor = "Moto e Ciclomotor"
acidentes_2014_2016["tipo de ocorrencia"] = acidentes_2014_2016["tipo de ocorrencia"].replace({
    "Motos e Ciclomotores": default_moto_ciclomotor
})


# In[87]:


acidentes_2014_2016.columns


# In[88]:


acidentes_2014_2016["geometry"] = acidentes_2014_2016.apply(lambda example: Point(example.longitude, example.latitude), axis=1)


# In[89]:


acidentes_2014_2016 = geopandas.GeoDataFrame(acidentes_2014_2016)


# Algumas datas se encontram no formato errado e não de acordo com os valores possíveis, logo
# é necesśario limpá-las.

# # Merges

# A ideia é juntar os datasets de infracoes com os de semaforo e dessa forma agregar uma localização às infrações que 
# tem semafóro associado.

# In[98]:


# remove todas as rows que possuem NaN na coluna
infracoes_2014_2016 = infracoes_2014_2016.dropna(subset=["numero_semaforo"])


# In[99]:


infracoes_2014_2016.dtypes


# In[100]:


infracoes_2014_2016[infracoes_2014_2016.numero_semaforo == "173"].head(10)


# In[101]:


semaforos[semaforos.semaforo == 173]


# Como é possível perceber acima, a localização dos semafóros com seus números condiz com os valores das infrações
# O que corrobora com a junção dos dados.

# In[138]:


infracoes_2014_2016.shape


# In[196]:


semaforos.columns


# In[180]:


infracoes_com_localizacao = geopandas.GeoDataFrame(infracoes_com_localizacao)


# ## Acidentes com Semaforo

# In[107]:


import geopy.distance


# In[108]:


def getIdOfTheLeastDistant(lat, lng, vector):
    data = {"semaforo_numero": 0, "distance": 999999}
    for element in vector:
        new_distance = geopy.distance.vincenty((lat, lng), (element[1], element[2])).km
        if new_distance < data["distance"]:
            data["semaforo_numero"] = element[0]
            data["distance"] = new_distance
    return int(data["semaforo_numero"])


# In[109]:


get_ipython().run_line_magic('load_ext', 'line_profiler')


# In[124]:


semaforo_locations = semaforos.loc[:, ["semaforo", "Latitude", "Longitude"]].values


# In[224]:


get_ipython().run_line_magic('lprun', '-f getIdOfTheLeastDistant acidentes_2014_2016.apply(lambda row: getIdOfTheLeastDistant(row["latitude"], row["longitude"], semaforo_locations), axis=1)')


# In[260]:


get_ipython().run_line_magic('lprun', '-f getIdOfTheLeastDistant acidentes_2014_2016.apply(lambda row: getIdOfTheLeastDistant(row["latitude"], row["longitude"], semaforo_locations), axis=1)')


# In[125]:


acidentes_2014_2016["numero_semaforo"] = acidentes_2014_2016.apply(lambda row: getIdOfTheLeastDistant(row["latitude"], row["longitude"], semaforo_locations), axis=1)


# In[126]:


infracoes_com_localizacao.columns


# In[127]:


acidentes_2014_2016.columns


# In[128]:


acidentes_2014_2016.shape


# # Working Datasets

# In[122]:


#writing them after cleaning and transforming everything
infracoes_2014_2016.to_csv("working_data/infracoes_2014_2016.csv", index=False)
acidentes_2014_2016.to_csv("working_data/acidentes_2014_2016.csv", index=False)
semaforos.to_csv("working_data/semaforos.csv", index=False)
fiscalizacao.to_csv("working_data/fiscalizacao.csv", index=False)
monitoramento.to_csv("working_data/monitoramente.csv", index=False)


# In[123]:


infracoes_2014_2016 = pandas.read_csv("working_data/infracoes_2014_2016.csv")


# In[276]:


infracoes_2014_2016.shape


# In[124]:


semaforos = pandas.read_csv("working_data/semaforos.csv")


# # Data Analysis

# In[125]:


acidentes_2014_2016["quantidade de vitimas"].value_counts()


# In[133]:


acidentes_2014_2016.groupby("bairro")["quantidade de vitimas"].sum().sort_values(ascending=False)


# In[142]:


acidentes_2014_2016.columns


# In[134]:


infracoes_com_localizacao.columns


# In[135]:


infracoes_com_localizacao.shape


# ## Infrações com Acidentes
# 
# Eu coloquei um join pelas infrações de forma que os acidentes sejam associados às infrações e não o contrário, senão se perderia muita informação
# de cada infração dada.

# In[132]:


infracoes_com_acidentes = acidentes_2014_2016.join(infracoes_com_localizacao, on="numero_semaforo", how="right", lsuffix='_left', rsuffix='_right')


# In[131]:


infracoes_com_acidentes


# # Visualização

# In[ ]:


from bokeh.plotting import figure, show, output_file, output_notebook
from bokeh.models import ColumnDataSource, Circle, HoverTool, Triangle, Square
from bokeh.tile_providers import CARTODBPOSITRON, STAMEN_TERRAIN
import datashader
import datashader.glyphs
import datashader.transfer_functions as tf
from holoviews.operation.datashader import datashade, shade, dynspread, rasterize


# In[ ]:


# map all dataframes to mercator
acidentes_2014_2016.crs = {'init': 'epsg:4326'}


# In[ ]:


acidentes_2014_2016 = acidentes_2014_2016.to_crs({ "init": "epsg:4326"})


# A projeção de lat lng utilizada pela CTTU parece conter um shift de alguns graus na longitude, então o lon0 
# deve ser modificado. Pra isso, vou ter de criar uma transformção de projeção própria.

# In[ ]:


from pyproj import Proj, transform
inProj  = Proj("+init=EPSG:4326")
outProj = Proj("+init=EPSG:3857 +lon_0=0")


# In[ ]:


transform(inProj, outProj, -34.925988, -8.029113) # (lon, lat)


# In[ ]:


acidentes_2014_2016["new_geometry"] = acidentes_2014_2016["geometry"].apply(lambda point: Point(transform(inProj, outProj, point.y, point.x)))


# In[ ]:


acidentes_2014_2016[["latitude", "longitude"]].head(5)


# In[ ]:


acidentes_2014_2016["geometry"].head(10)


# In[ ]:


acidentes_2014_2016 = acidentes_2014_2016.to_crs({ "init": "epsg:3857"})


# In[ ]:


acidentes_2014_2016[["new_geometry","geometry", "latitude", "longitude"]].head(10)


# In[ ]:


monitoramento.crs = {'init': 'epsg:4326'}


# In[ ]:


monitoramento = monitoramento.to_crs({ "init": "epsg:3857"})


# In[ ]:


fiscalizacao.crs = {'init': 'epsg:4326'}


# In[ ]:


fiscalizacao = fiscalizacao.to_crs({ "init": "epsg:3857"})


# ## Display all data inside recife

# In[ ]:


p = figure(y_range=(-805000, -1025500), x_range=(-3950000, -3850000),
          x_axis_type="mercator", y_axis_type="mercator")

p.add_tile(CARTODBPOSITRON)
p.title.text = "Localização dos acidentes registrados pela CTTU entre 2014 e 2016"

#crashes

crash_source = ColumnDataSource(
    data=dict(
        lat=acidentes_2014_2016.geometry.y.tolist(),
        lon=acidentes_2014_2016.geometry.x.tolist(),
        descricao=acidentes_2014_2016.descricao.tolist()
    )
)

crash_circle = Circle(x="lon", y="lat", fill_alpha=0.5, line_color=None, fill_color="red", size=5)
crash_renderer = p.add_glyph(crash_source, crash_circle)

hover_crash = HoverTool(
    tooltips=[
        ("(lat,lng)", "(@lat, @lon)"),
        ("descricao", "@descricao"),
    ],
    renderers=[crash_renderer]
)

p.add_tools(hover_crash)

#monitoring

monitoring_source = ColumnDataSource(
    data=dict(
        lat=monitoramento.geometry.y.tolist(),
        lon=monitoramento.geometry.x.tolist(),
        name=monitoramento.nome.tolist()
    )
)



monitoring_circle = Square(x="lon", y="lat", fill_color="yellow", size=10)
monitoring_renderer = p.add_glyph(monitoring_source, monitoring_circle)

hover_monitoring = HoverTool(
    tooltips=[
        ("(lat,lng)", "(@lat, @lon)"),
        ("name", "@name"),
    ],
    renderers=[monitoring_renderer]
)

p.add_tools(hover_monitoring)

# fiscalizacao

fiscalizacao_source = ColumnDataSource(
    data=dict(
        lat=fiscalizacao.geometry.y.tolist(),
        lon=fiscalizacao.geometry.x.tolist(),
        equipamento=fiscalizacao.EQUIPAMENTO.tolist(),
        velocidade=fiscalizacao.VELOCIDADE.tolist()
    )
)

fiscalizacao_circle = Triangle(x="lon", y="lat", fill_color="black", size=10)
fiscalizacao_renderer = p.add_glyph(fiscalizacao_source, fiscalizacao_circle)

hover_fiscalizacao = HoverTool(
    tooltips=[
        ("(lat,lng)", "(@lat, @lon)"),
        ("equipamento", "@equipamento"),
        ("velocidade", "@velocidade")
    ],
    renderers=[fiscalizacao_renderer]
)

p.add_tools(hover_fiscalizacao)

#configuration

output_notebook() #in order to plot inline
show(p)


# In[ ]:


acidentes_2014_2016.columns

