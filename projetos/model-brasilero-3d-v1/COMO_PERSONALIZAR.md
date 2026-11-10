# Como personalizar o boneco (model-brasilero-3d-v1)

O boneco funciona como um skin de Minecraft: **toda a pele, rosto e roupa vêm de uma única imagem, `skin.png` (128x128)**.
Você desenha nessa imagem, salva, e o boneco veste o desenho.

## O que tem nesta pasta

| Arquivo | Para que serve |
|---|---|
| `model-brasilero-3d-v1.blend` | O boneco (Blender 5.2 ou mais novo), em T-pose. Lê o `skin.png` desta mesma pasta. |
| `skin.png` | A skin em uso. **É este arquivo que você edita.** (Agora: pele rosa, rosto preto, camisa verde, bermuda azul, chuteira preta, cravos brancos.) |
| `template/mapa_template_1024.png` | Mapa grande (8x) com o nome e a posição de cada área e a malha desenhada por cima. Use como referência. |
| `template/areas_128.png` | Cada área pintada de uma cor, no tamanho real (128x128). Útil como camada-guia no editor. |
| `template/layout.json` | Posição exata (x, y, largura, altura) de cada área, em pixels. |
| `preview.png` | Como o boneco ficou com a skin atual. |
| `scripts/build_skin_system.py` | Script que gerou tudo (para refazer ou mudar o layout). |

## Passo a passo

1. **Faça uma cópia** do `skin.png` antes de mexer (ex.: `skin_original.png`).
2. Abra o `skin.png` num editor de imagem:
   - **Photopea** (grátis, no navegador: photopea.com), **Krita** (grátis) ou **Aseprite** (pago, feito para pixel art). Photoshop também serve.
3. (Opcional) Coloque `template/areas_128.png` numa camada por cima, com transparência ~40%, para ver os limites. **Esconda essa camada antes de salvar.**
4. Pinte usando o lápis/pincel **sem suavização** (1 px, sem anti-aliasing), para manter o visual pixelado.
5. Salve como **PNG, 128x128, com o nome `skin.png`**, na mesma pasta do `.blend` (por cima do antigo).
6. No Blender, passe o mouse sobre a área 3D e aperte **Alt+R** (recarregar imagens). O boneco atualiza.
   - Para ver as cores no Blender: modo de visualização **Material Preview** (tecla Z > Material Preview) ou Solid com cor "Texture".

Dica: quer vários personagens? Guarde cada skin com um nome (`skin_brasil.png`, `skin_argentina.png`...) e, para usar uma,
copie por cima do `skin.png`.

## Mapa das áreas (pixels, contando do canto superior esquerdo)

| Área | x | y | largura x altura | O que é |
|---|---|---|---|---|
| ROSTO | 0 | 0 | 48x48 | Frente do rosto (olhos, nariz, boca). Esquerda da imagem = lado direito do boneco (como olhar de frente). |
| CABECA_LADOS_TRAS | 48 | 0 | 48x24 | Bochechas, laterais e trás da cabeça. |
| COURO_CABELUDO | 48 | 24 | 48x24 | Topo da cabeça (careca). Fica coberto quando houver cabelo. |
| ORELHA_ESQ / DIR | 96 / 112 | 0 | 16x12 cada | Orelhas. |
| PESCOCO | 96 | 12 | 32x8 | Pescoço. |
| MAO_ESQ / DIR | 96 / 112 | 20 | 16x14 cada | Mãos. |
| CADARCO_ESQ / DIR | 96 / 112 | 34 | 16x14 cada | Língua e cadarço da chuteira. |
| CAMISA_FRENTE | 0 | 48 | 40x40 | Frente do tronco (o "V" rosa é o decote; pinte por cima se quiser gola fechada). |
| CAMISA_COSTAS | 40 | 48 | 40x40 | Costas (bom lugar para nome e número). Esquerda da imagem = lado esquerdo do boneco (como olhar de trás). |
| BRACO_ESQ / DIR | 80 | 48 / 58 | 48x10 cada | Manga + antebraço. Na horizontal: esquerda = ombro, direita = punho. |
| BERMUDA_CINTURA | 80 | 68 | 48x20 | Elástico e quadril, dando a volta no corpo (centro = frente). |
| BERMUDA_PERNA_ESQ / DIR | 0 / 24 | 88 | 24x16 cada | Pernas da bermuda. |
| SOLA_ESQ / DIR | 0 / 24 | 104 | 24x16 cada | Sola da chuteira. |
| CRAVOS_ESQ / DIR | 0 / 24 | 120 | 24x8 cada | Cravos (todos os cravos de um pé usam a mesma área). |
| PERNA_ESQ / DIR | 48 / 68 | 88 | 20x40 cada | Pernas (pele). |
| CHUTEIRA_ESQ / DIR | 88 / 108 | 88 | 20x26 cada | Corpo da chuteira. |

"ESQ" e "DIR" são o lado **do boneco** (a esquerda dele, não a sua).

## Limites desta versão

- **Rosto:** a área ROSTO cobre só as faces que olham bem para a frente (o miolo do rosto). Testa e bochechas estão em CABECA_LADOS_TRAS. Por isso, no teste, o preto aparece como uma "máscara".
- **Forma não muda pelo desenho.** A imagem muda cor e desenho; cabelo, boné etc. serão peças 3D separadas (próxima etapa: 6 cabelos para escolher).
- **Ainda sem esqueleto** (próxima etapa, para animações).
- Cada pixel conta: 128x128 é pouco espaço, igual a um jogo de N64. Detalhes muito finos podem não aparecer.
