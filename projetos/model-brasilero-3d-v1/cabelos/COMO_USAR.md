# Cabelos (model-brasilero-3d-v1/cabelos)

7 cortes x 5 cores = 35 versões do boneco, cada uma já com o sistema de rostos.
Todos os cortes são originais, low-poly no estilo N64, com textura pixelada 64x64.

## Cortes e cores

Cortes: 01 liso-repartido, 02 jogador-degrade, 03 raspado, 04 cacheado-curto, 05 crespo-curto,
06 espetado-gel, 07 mullet.

Cores: loiro-natural, loiro-pintado (platinado, tom da foto de referência), ruivo, preto, castanho.

Nome dos arquivos: `<Nº>-<corte>_<cor>.blend`, por exemplo `07-mullet_ruivo.blend`.

## O que tem na pasta

| Pasta/arquivo | Para que serve |
|---|---|
| `*.blend` (35) | Boneco completo com o cabelo. Objeto `Cabelo` (filho da Cabeca), material `Cabelo`. |
| `texturas/` (35) | Textura de cada corte em cada cor (`<corte>_<cor>.png`, 64x64). |
| `web/` (35) | Mesmas versões em `.glb` para jogo web, tudo embutido. Rosto funciona igual ao `rostos/web`. |
| `previews/` | `print1_liso-repartido_5-cores.png`, `print2_castanho_7-cortes.png`, `todas_35_versoes.png`. |
| `scripts/` | Código que gerou tudo. |

## Importante: não separe as pastas

Os `.blend` daqui leem a pele e os rostos da pasta vizinha: `../rostos/skin.png` e `../rostos/rostos_atlas.png`.
Se você mexer no `skin.png` de `rostos/`, todas as 35 versões mudam juntas (Alt+R no Blender).
Se mover a pasta `cabelos` sozinha para outro lugar, a pele fica rosa choque (textura não encontrada).
Os `.glb` não têm esse problema: levam tudo dentro.

## Trocar a cor na mão

No Blender, no material `Cabelo`, troque a imagem do nó de textura por outra de `texturas/`.
Para criar uma cor nova, pinte por cima de qualquer PNG de `texturas/` mantendo os 4 tons
(escuro, médio, claro, brilho) e as partes transparentes (risca do liso e o degradê do jogador).

## Regerar

`python3 scripts/build_cabelos.py <../rostos/model-brasilero-3d-rostos.blend> <pasta cabelos>` (Blender 5.2.3 como
módulo `bpy`). Cores em `CORES`, formato de cada corte em `corte()`. Exportar web: `scripts/export_web.py <blend> <glb>`.

## Limites

- A franja cobre a parte de cima da sobrancelha em alguns cortes (a borda do couro cabeludo já ficava ali).
- Acima das orelhas o cabelo para antes, para não atravessar a orelha; ali aparece pele.
- Ainda sem esqueleto: o cabelo é filho da cabeça, então vai acompanhar quando o rig existir.
