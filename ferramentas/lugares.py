"""Lugares do folheto do Sesc Bertioga com coordenadas reais (OSM) -> PLACES do app.
Uso: python3 -I places.py data.json index.html places.json
"""
import json, math, re, sys
D = json.load(open(sys.argv[1]))
html = open(sys.argv[2]).read()
OLD = {p['id']: p for p in json.loads(re.search(r'const PLACES = (\[.*?\]);', html).group(1))}
REF = D['REF']; K = D['K']; E0 = D['E0']; N1 = D['N1']; MW = D['MW']; MH = D['MH']
COS = math.cos(math.radians(REF[0]))
def xy(lat, lng):
    e = (lng - REF[1]) * 111320 * COS; n = (lat - REF[0]) * 110574
    return ((e - E0) * K / MW, (N1 - n) * K / MH)
def off(lat, lng, de, dn): return (lat + dn / 110574, lng + de / (111320 * COS))
# praia: eixo ao longo da cerca (leste-nordeste) e normal para o mar
AL = (0.892, 0.453); SEA = (0.453, -0.892)
def beach(along, sea):
    return off(-23.830782, -46.111484, AL[0] * along + SEA[0] * sea, AL[1] * along + SEA[1] * sea)

# id, nº, nome, categoria, (lat,lng), descrição (vazia = mantém a antiga)
L = [
 ('cenico', 1, 'Espaço Cênico', 'conv', (-23.829430, -46.111316), ''),
 ('brincar', 2, 'Espaço de Brincar', 'conv', (-23.829835, -46.111410), ''),
 ('biblioteca', 3, 'Biblioteca e Balcão de Atendimento', 'conv', (-23.829504, -46.111611), ''),
 ('tecnologia', 4, 'Espaço de Tecnologia e Artes', 'conv', (-23.829576, -46.111224), ''),
 ('jardimcafe', 5, 'Jardim Café', 'conv', (-23.829681, -46.111156), ''),
 ('jardim', 6, 'Jardim da Convivência', 'conv', (-23.829600, -46.111400), ''),
 ('lanchonete', 7, 'Lanchonete', 'conv', (-23.829855, -46.111067), ''),
 ('loja', 8, 'Loja Sesc', 'conv', (-23.829495, -46.111273), ''),
 ('marquise', 9, 'Marquise do Restaurante', 'conv', (-23.829270, -46.111600), ''),
 ('restaurante', 10, 'Restaurante', 'conv', (-23.828990, -46.111700), ''),
 ('salatv', 11, 'Sala de TV', 'conv', (-23.829784, -46.111443), 'Na Área de Convivência.'),
 ('convivencia', 12, 'Salas de Jogos', 'conv', (-23.829675, -46.111511), 'Jogos, revistas e livros emprestados no balcão (9h às 22h30).'),
 ('prainha', 13, 'Prainha', 'conv', (-23.829920, -46.110860), 'Área de areia ao lado da Área de Convivência.'),
 ('campo', 14, 'Campo de Futebol Oficial', 'esp', (-23.824945, -46.110150), 'Bolas emprestadas na Governança.'),
 ('bocha', 15, 'Cancha de Bocha', 'esp', (-23.825725, -46.112201), ''),
 ('tenis', 16, 'Quadra e Paredão de Tênis', 'esp', (-23.825928, -46.113170), 'Raquetes emprestadas na Governança.'),
 ('pista', 17, 'Pista para Caminhada', 'esp', (-23.825150, -46.111050), 'Trilhas de terra entre o campo e os minicampos.'),
 ('ginasio', 18, 'Quadra Poliesportiva (Ginásio)', 'esp', (-23.826053, -46.111955), ''),
 ('curumim', 19, 'Curumim / Sala Múltiplo Uso 3', 'esp', (-23.824728, -46.113984), ''),
 ('lago', 20, 'Lago', 'esp', (-23.823184, -46.112794), ''),
 ('minicampo', 21, 'Minicampos de Futebol', 'esp', (-23.825170, -46.112510), ''),
 ('minigolfe', 22, 'Minigolfe', 'esp', (-23.824462, -46.113125), ''),
 ('xadrez', 23, 'Xadrez Gigante', 'esp', (-23.826395, -46.112193), ''),
 ('gmf', 24, 'Galpão da GMF', 'esp', (-23.824784, -46.112305), 'Ginástica multifuncional.'),
 ('seixos', 25, 'Caminho dos Seixos Rolados', 'corpo', (-23.828790, -46.108930), ''),
 ('corpo', 26, 'Espaço do Corpo', 'corpo', (-23.828586, -46.109054), ''),
 ('yinyang', 27, 'Espaço Yin e Yang', 'corpo', (-23.828700, -46.109060), ''),
 ('redario', 28, 'Redário', 'corpo', (-23.829428, -46.108965), ''),
 ('oficinas', 29, 'Oficinas de Criação', 'corpo', (-23.823918, -46.111445), ''),
 ('ginastica', 30, 'Sala de Ginástica', 'corpo', (-23.828881, -46.108658), ''),
 ('brinqagua', 31, 'Brinquedo Aquático', 'cri', (-23.827895, -46.109402), '9h30 às 17h.'),
 ('musical', 32, 'Brinquedo Musical', 'cri', (-23.825633, -46.113283), ''),
 ('arvore', 33, 'Casa da Árvore', 'cri', (-23.827905, -46.109755), ''),
 ('cordas', 34, 'Circuito de Cordas', 'cri', (-23.828057, -46.109734), ''),
 ('capela', 35, 'Capela', 'hist', (-23.828814, -46.109539), ''),
 ('caicara', 36, 'Casa do Caiçara', 'hist', (-23.823578, -46.110151), ''),
 ('gruta', 37, 'Gruta', 'hist', (-23.826857, -46.109128), 'Gruta de Nossa Senhora de Lourdes.'),
 ('piscinas', 38, 'Piscinas (Parque Aquático)', 'agua', (-23.829657, -46.110383), ''),
 ('bochapraia', 39, 'Bocha (praia)', 'praia', beach(-170, 30), 'Na areia, perto do estacionamento.'),
 ('estacao', 40, 'Estação Vivência, Estação Praia e Palco', 'praia', beach(28, 32), ''),
 ('portariapraia', 41, 'Portaria da Praia e Quiosque de Locação', 'praia', beach(0, 6), ''),
 ('quadras', 42, 'Quadras de Vôlei, Tênis de Praia, Beach Tennis e Futebol de Praia', 'praia', beach(115, 36), ''),
 ('praia', None, 'Praia', 'praia', beach(10, 70), ''),
 ('jerivas', 43, 'Recanto dos Jerivás', 'quiosq', (-23.823331, -46.110820), ''),
 ('suina', 44, 'Suinã e Bromélias', 'quiosq', (-23.824770, -46.111860), 'Quiosques no bosque, perto da pista de caminhada.'),
 ('sollua', 45, 'Sol e Lua', 'quiosq', (-23.830077, -46.110543), ''),
 ('cea', 46, 'Centro de Educação Ambiental', 'sust', (-23.828155, -46.109228), ''),
 ('baleia', 47, 'Nicho da Baleia', 'sust', (-23.828416, -46.109227), ''),
 ('viveiro', 48, 'Viveiro de Plantas', 'sust', (-23.822688, -46.110945), 'Com orquidário e a Trilha do Cacau.'),
 ('recepcao', 50, 'Central de Atendimento / Recepção', 'hosp', (-23.827520, -46.113280), ''),
 ('estac', 51, 'Estacionamento de Hóspedes', 'hosp', (-23.823600, -46.113600), ''),
 ('vestiario', 52, 'Vestiário', 'dia', (-23.829200, -46.113060), 'Para quem vem passar o dia.'),
 ('estacdia', 53, 'Estacionamento (passeio de um dia)', 'dia', (-23.830750, -46.112880), ''),
 ('convencoes', 54, 'Sala de Convenções', 'adm', (-23.829600, -46.112990), ''),
 ('multiuso', 55, 'Salas Múltiplo Uso 1 e 2', 'adm', (-23.829950, -46.112900), ''),
 ('mirante', 56, 'Mirante', 'vis', (-23.829289, -46.109929), ''),
 ('totem', 57, 'Totem de Autoatendimento', 'auto', (-23.829550, -46.111180), 'Há totens também na Governança, perto do Ginásio e no Galpão da GMF.'),
 ('lavanderia', 58, 'Máquinas de Lavar e Secar', 'gov', (-23.828538, -46.111409), ''),
 ('portaria', None, 'Portaria principal', 'hosp', (-23.827746, -46.113366), ''),
 ('governanca', None, 'Serviços e Governança', 'gov', (-23.826203, -46.113672), ''),
 ('senac', None, 'Senac', 'adm', (-23.826482, -46.113574), 'Escola do Senac, vizinha da Governança.'),
]
# repetições de um mesmo número em outros pontos (aparecem no mapa, não na lista)
EXTRA = [
 ('totem', (-23.826250, -46.113600)), ('totem', (-23.825900, -46.112120)), ('totem', (-23.824700, -46.112550)),
 ('restaurante', (-23.829211, -46.111919)),
 ('lavanderia', (-23.827412, -46.111322)), ('lavanderia', (-23.827209, -46.110817)), ('lavanderia', (-23.826546, -46.110917)),
 ('lavanderia', (-23.826710, -46.111687)), ('lavanderia', (-23.827226, -46.112296)), ('lavanderia', (-23.827289, -46.109488)),
 ('lavanderia', (-23.826573, -46.109389)), ('lavanderia', (-23.826768, -46.110190)),
 ('estacdia', (-23.830995, -46.112784)),
]
out = []
for id_, num, n, cat, (lat, lng), d in L:
    x, y = xy(lat, lng)
    old = OLD.get(id_, {})
    out.append({'id': id_, 'num': num, 'n': n, 'cat': cat, 'x': round(x, 5), 'y': round(y, 5), 'lat': round(lat, 6), 'lng': round(lng, 6), 'd': old.get('d') or d})
ids = {p['id'] for p in out}
missing = [i for i in OLD if i not in ids]
assert not missing, missing
dupes = []
for id_, (lat, lng) in EXTRA:
    x, y = xy(lat, lng); dupes.append({'of': id_, 'x': round(x, 5), 'y': round(y, 5)})
json.dump({'places': out, 'dupes': dupes}, open(sys.argv[3], 'w'), ensure_ascii=False)
print(len(out), 'lugares,', len(dupes), 'repetições')
