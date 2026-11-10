# Projetos

## jogador-n64 (ativo)
Pasta: `projetos/jogador-n64/`

**Origem:** `entrada/modelo-original.zip`: rip do Young Link de *Smash Remix* (N64) enviado pelo Samuel.
Dentro: um `.rar` (RAR5) com `young link.obj`/`.mtl` (304 vértices, 497 faces, 20 materiais, sem rig)
e texturas BMP/PNG minúsculas (16x16 e 32x32). O `.mtl` aponta para `F:\Nueva carpeta\`.

**Versão atual:** `atual/` = v7 (abrir `atual/model-by-samuel.blend`; texturas em `atual/textures/`,
caminhos relativos). Blender **5.2.3 LTS** (não abre em 4.x ou anterior).

| Versão | Arquivo em `versoes/` | O que é | Preview |
|---|---|---|---|
| v1 | `v1-blend-original.zip` | OBJ convertido para .blend, texturas externas, filtro Closest | `previews/v1.png` |
| v2 | `v2-sem-espada-escudo.zip` | Sem espada (lâmina, bainha, cabo) e sem os 2 escudos | `previews/v2.png` |
| v3 | `v3-dummy-manequim.zip` | Manequim cinza neutro em T-pose, mesmas medidas/juntas, feito de primitivas | `previews/v3-dummy.png` |
| v4 | `v4-futebol-v1.zip` | 1ª versão futebol: cabelo preto, camisa preta, bermuda e chuteira brancas (cores lisas) | `previews/v4.png` |
| v5 | `v5-futebol-v2.zip` | Rosto humano novo pintado do zero, orelhas humanas, pele mais viva, bermuda refeita com elástico, chuteira com sola, 6 cravos, língua e cadarço | `previews/v5.png` |
| v6 | `v6-futebol-v3-corte-jogador.zip` | Corte de jogador original: laterais em degradê + mechas para frente, castanho escuro | `previews/v6.png` |
| v7 | `v7-casual-v4-liso-repartido.zip` | **ATUAL.** Cabelo liso infantil repartido de lado (original), resto igual à v5/v6 | `previews/v7.png` |

O Samuel gostou muito da v5 ("gostei, gostei mesmo").

**Como regerar (scripts em `scripts/`, Python com o módulo `bpy` 5.2.3):**
- v1: `build_blend.py <pasta com young link.obj/.mtl> <saida>` (env `TEXTURES_SRC` = pasta das texturas PNG)
- v2: mesmo script com `REMOVE="3rr,Mesh.002,Mesh.008,Mesh.010,Mesh.014,Mesh.016"`
- v3: `build_dummy.py <v1.blend> <saida.blend>`
- v4: `build_football.py <v2.blend> <saida>`
- v5/v6/v7: `build_kit_v2.py` / `build_kit_v3.py` / `build_kit_v4.py <v2.blend> <saida>`; as texturas novas são
  geradas pelo script; a pasta de texturas da v2 precisa estar ao lado do .blend de entrada
- Prévias: `views.py <blend> <png> <cx,cy,cz> <escala_orto> front,side,back,q [px]`
- Parâmetros ajustáveis por variáveis de ambiente (`HAIR_*`, `EAR_*`, `Z_*`, `WAIST_*`, `HIP_*`, `LEG_R`...).
  Ex.: `HAIR_PART_AZ` negativo troca o lado do repartido na v7.

**Mapa da malha original (nomes dos objetos no v2):**
cabeça `Mesh.003` (mat 0 cabelo, 1 pele/olho, 2 boca, 3 gorro), pescoço `Mesh.004`, tronco `Mesh.001`,
braços `Mesh`(esq.) / `Mesh.005`(dir.), mãos `Mesh.015`/`Mesh.011`, pernas `Mesh.007`/`Mesh.006`,
pés `Mesh.013`/`Mesh.009`, saia `Mesh.012`. Removidos na v2: espada `3rr`, `Mesh.002`, `Mesh.008`, `Mesh.010`;
escudos `Mesh.014`, `Mesh.016`. Na v5+ os objetos foram renomeados (Cabeca, Bermuda, Chuteira.L...).
Convenção: Z para cima, frente = -Y, esquerda do personagem = +X. Altura ≈ 0,45 unidades.

**Pendências / ideias:**
- v7: o cabelo ficou levemente despenteado; dá para alinhar (menos contraste nos fios, franja mais uniforme).
- Formato da cabeça ainda é o da malha original (proporção infantil N64).
- Sem rig. Possível próximo passo: armature para animar.

## skin-system / model-brasilero-3d (protótipo v1 pronto em 2026-11-08)
Pasta: `projetos/model-brasilero-3d-v1/` (ler `COMO_PERSONALIZAR.md` lá dentro). Gerado por `scripts/build_skin_system.py` a partir do v7 do jogador-n64.
Sistema estilo skin do Minecraft sobre o boneco v7 do `jogador-n64`: um `skin.png` 128x128 com áreas fixas
(rosto, pele, camisa, bermuda, chuteira), 6 cabelos originais trocáveis e esqueleto para animação.
Pasta prevista: `projetos/skin-system/` (com `skins/` para cada personagem). Detalhes no histórico de 2026-11-08.

## Atualização 2026-11-09 (skin-system)
- Cabelos confirmados: 7 (ver `notas.md`). Ainda não feitos.
- **Sistema de rostos animados: PRONTO (2026-11-09).** Pasta `projetos/model-brasilero-3d-v1/rostos/` (ler `COMO_USAR.md`).
  5 tipos de rosto x 5 animações x 5 frames. Animações: 1 piscada de um olho, 2 piscada dos dois olhos,
  3 cara de força, 4 cara de dor, 5 cara de felicidade. Frames: 1 e 5 = rosto padrão, 3 = expressão completa,
  2 e 4 = transição. Detalhes no histórico de 2026-11-09.

### rostos (feito em 2026-11-09)
- Arquivos: `model-brasilero-3d-rostos.blend` (lê `//skin.png` e `//rostos_atlas.png`), `skin.png` (v1 com área ROSTO
  em pele lisa), `rostos_atlas.png` (1200x240: 5 blocos 240x240 por tipo; linha = animação, coluna = quadro; 48x48),
  `rostos_guia.png`, `rostos.json`, `web/model-brasilero-3d-rostos.glb`, `web/demo_web.html` (offline, testada),
  `previews/rostos_grade.png` e `rostos_animados.gif`, `scripts/`.
- Tipos (0-4): clássico, animado, focado, sardento, tranquilo (todos originais, desenhados por código).
- Como funciona: objeto `Rosto_Expressao` = cópia das faces da frente da cabeça (normal.y < -0.12), 0,6 mm para fora,
  UV em projeção frontal. Material lê as propriedades do objeto `tipo_rosto`, `animacao`, `quadro` (nó Attribute
  tipo Object). 5 Actions `Rosto_<anim>` (quadros 1-11, constante, 2 quadros da cena por quadro de rosto, 10 fps).
- Web: UV aponta para o quadro (0,0,0); `map.offset.set((tipo*5+quadro)/25, animacao/5)`. Actions não vão pro glb.
- Regerar: `build_faces.py <saida> calib.json` -> `build_rostos_blend.py <v1.blend> <v1 skin.png> <atlas> <saida>`
  -> `export_web.py <blend> <glb>` -> `scripts/web/build_demo.py <glb> <html>` (precisa three@0.170.0 e esbuild via npm).
  Posição de olhos/boca em `calib.json` (eye_y 24, eye_dx 9, brow_y 19, mouth_y 36).
- Limites: borda do couro cabeludo cobre o alto da testa; sobrancelha com cor fixa por tipo.
- Correção registrada: a área ROSTO da v1 JÁ era projeção frontal (Sofia leu o mapa errado e disse que era
  irregular). O UV da skin não foi mudado; a projeção nova é só da camada de expressão.

### cabelos (feito em 2026-11-09)
Pasta: `projetos/model-brasilero-3d-v1/cabelos/` (ler `COMO_USAR.md`). 35 versões = 7 cortes x 5 cores, cada uma
é o boneco com rostos + objeto `Cabelo` (filho da Cabeca), material `Cabelo` lendo `//texturas/<corte>_<cor>.png`.
- Cortes: 01 liso-repartido, 02 jogador-degrade, 03 raspado, 04 cacheado-curto, 05 crespo-curto, 06 espetado-gel, 07 mullet.
- Cores: loiro-natural, loiro-pintado (platinado da foto de referência do Samuel), ruivo, preto, castanho.
- Arquivos: `<NN>-<corte>_<cor>.blend` (35), `texturas/` (35 PNG 64x64, 4 tons + transparente), `web/` (35 .glb,
  cabelo com alphaMode MASK), `previews/` (print1 liso nas 5 cores, print2 castanho nos 7 cortes, todas_35_versoes),
  `scripts/` (hair_lib.py, build_cabelos.py, render_cabelos.py, export_web.py).
- Os .blend leem `../rostos/skin.png` e `../rostos/rostos_atlas.png`: não separar as pastas.
- Como é feito: casca em grade (colunas x anéis) colada no crânio por raios do centro (0.002,-0.003,0.385) contra
  Couro_Cabeludo+Cabeca; linha do cabelo = borda do couro cabeludo - 1,2 mm, mas acima das orelhas (z>=0.3895 em
  azimute 1.68-2.15). Detalhes: espetos (pirâmides), cachos (pirâmides baixas de 6 lados), mechas, aneis extras (mullet).
- Ajustes feitos na conferência: raspado e degradê precisaram de casca >= 2 mm e grade mais densa (a careca furava);
  degradê só rareia nas laterais/nuca; levantar a lateral do mullet expunha a borda da careca, foi desfeito.
- Regerar: `build_cabelos.py <rostos/model-brasilero-3d-rostos.blend> <cabelos/>`; exportar: `export_web.py`.

### cabelos-v2 (2026-11-09, ~19:50) — SUBSTITUI a v1 na prática
Samuel achou a v1 (`cabelos/`) "horrível" e mandou uma imagem de referência: cabelo low-poly feito de mechas
grossas e pontudas em camadas (estilo anime). Refeito em `projetos/model-brasilero-3d-v1/cabelos-v2/` (pasta NOVA;
a `cabelos/` antiga continua lá até ele aprovar apagar). Mesmos 7 cortes x 5 cores, mesmos nomes de arquivo.
- Técnica: casca fina e escura por baixo (sombra entre mechas) + mechas em cunha com quina (`hair_locks.py`:
  caminho em arco pela cabeça, seção triangular, afina até a ponta, sombreamento suave). Cacheado = cachos
  arredondados (elipsoides achatados, `blob`). Espetado = mechas largas jogadas pra trás + topete na frente.
  Textura 64x64: metade de cima = mechas, metade de baixo = casca.
- Conferência: `check_cabelos.py` (sem faces quebradas, sem mecha solta; "dentro da cabeça" = borda da casca, ok).
  35 renders a partir dos .blend salvos, sem textura faltando. Prints refeitos e enviados.
- Ponto fraco conhecido: espetado de frente forma "coroa" de pontas no alto.
- Regerar: `scripts/build_cabelos_v2.py <rostos/model-brasilero-3d-rostos.blend> <cabelos-v2/>`.

### cabeça normal + cabelos-v3 (2026-11-09, ~20:30) — VERSÃO ATUAL DOS CABELOS
Samuel percebeu que o boneco tinha um "capacete rosa": o objeto `Couro_Cabeludo` era a base do cabelo antigo
(cor de pele, com aba na frente e franja em zigue-zague). Sem ele a cabeça é só a máscara do rosto.
- Corrigido com `fix_cranio.py`: novo objeto `Cranio` (casca convexa da borda do rosto + elipsoide, centro
  (0.0015,-0.003,0.383), raios (0.0465,0.0545,0.0545)), sem faces na frente do rosto abaixo de z 0.397,
  UV num retângulo todo cor de pele da skin (52,24,23x18). `Couro_Cabeludo` removido.
- Modelo careca com crânio: `projetos/model-brasilero-3d-v1/rostos/model-brasilero-3d-rostos-cranio.blend` (novo;
  o `model-brasilero-3d-rostos.blend` antigo não foi mexido e ainda tem o capacete).
- Cabelos refeitos sobre o crânio: `projetos/model-brasilero-3d-v1/cabelos-v3/` (mesmos 35 nomes, .glb, prints).
  Linha do cabelo agora explícita (`HAIRLINE_CRANIO` em hair_lib.py). Espetado ganhou franja de 5 mechas
  (acabou a "coroa"); mullet com nuca longa só atrás (|a|>2.45).
- Pastas antigas `cabelos/` (v1) e `cabelos-v2/` continuam lá, esperando aprovação para apagar.

### cabelos-v4 (2026-11-09, ~21:00) — VERSÃO ATUAL
Samuel apontou uma "placa" entre o rosto e o resto da cabeça. Eram faces grandes e retas do crânio v3: uma de cada
lado (têmpora até mandíbula), uma tampa embaixo do queixo atravessando o pescoço e uma fresta na têmpora.
Corrigido em `fix_cranio.py`: só remove faces na frente do MIOLO do rosto (|x|<0.036), tira a tampa de baixo do
queixo (normal.z<-0.45, z<0.372, y<-0.004) e a nuca afina em direção ao pescoço (NECK_Y=0.008, até z 0.336).
Tentativa de deixar a parte de baixo do crânio mais cheia ficou com cara de capacete e foi desfeita.
- Arquivos: `projetos/model-brasilero-3d-v1/cabelos-v4/` (35 .blend, .glb, prints) e
  `rostos/model-brasilero-3d-rostos-cranio-v2.blend` (careca). Pastas `cabelos/`, `-v2`, `-v3` e
  `rostos/...-cranio.blend` são antigas, esperando aprovação pra apagar.

### guia Vestiário Pixel + skin de exemplo (2026-11-09, ~21:30)
- Samuel mandou fotos de um uniforme real de clube (com escudo, marca de material esportivo e patrocinadores) e pediu
  logos "parecidos no limite". Sofia recusou reproduzir uniforme/logos reais ou imitações; ofereceu time fictício.
  Ele preferiu aprender a fazer a própria textura.
- Página interativa publicada (artifact "Vestiário Pixel"): mapa clicável da skin, paleta de 4 tons, quadro de treino
  40x40, números 5x7, atlas de rostos clicável, passo a passo no Photopea (camisa, bermuda, meião, chuteira, pele,
  rostos, cabelo), checklist. Cópia em `projetos/model-brasilero-3d-v1/skins/vestiario-pixel.html`.
- Skin de exemplo do time inventado "Capivara EC" (verde-água, faixa laranja, escudo de capivara, nº 7):
  `skins/skin_capivara.png` e variação com outro tom de pele `skins/skin_capivara_pele2.png`.
- Dado útil: a manga na área BRACO vai do x 80 ao ~107; do 108 em diante é antebraço. Trocar a pele = balde não contíguo
  na cor (242,160,172) troca 6.554 pixels de uma vez.

### skin feita pelo Samuel (2026-11-09, ~21:50)
- Ele pintou a própria skin (camisa preta com faixa diagonal branca, cruz vermelha, "VASCO 10" nas costas) e pediu
  pra aplicar e renderizar com mullet loiro platinado + rosto Tranquilo (tipo 4). Feito só o render pra ele ver.
- Arquivos em `model-brasilero-3d-v1/skins/`: `skin_vasco_original.png` (o dele, intacto), `skin_vasco.png` (cópia com a
  área CRAVOS preenchida de branco, que estava 100% transparente), e os renders `skin_vasco_render_corpo.png`/`_cabeca.png`.
- Feedback dado: preto puro (0,0,0) sem tons vira silhueta chapada; nome nas costas fica escondido pelo mullet.

### Prompt do Jarvis + origem do modelo (2026-11-09, ~22:00)
- `projetos/model-brasilero-3d-v1/JARVIS_PROMPT.md`: documento para a outra IA do Samuel (Jarvis) implementar no jogo
  (skin, rostos com fórmula de offset, cabelos, materiais, regra de texturas Nearest/flipY false, checklist, o que
  pode e não pode ir pro jogo).
- **Origem (importante):** 11 peças do corpo vêm do rip do Young Link (Smash Remix): Cabeca, Pescoco, Camisa_Tronco,
  Braco.L/R, Mao.L/R, Perna.L/R, Chuteira.L/R (mapa RENAME no build_kit_v4.py). Rosto_Expressao é cópia da Cabeca.
  Nossas (feitas do zero): Bermuda, Orelha.L/R, Chuteira_Sola, Chuteira_Cadarco, Cranio, Cabelo, todas as texturas,
  atlas de rostos, layout da skin. Samuel quer o BRASILERO 100% original: proposta = refazer o corpo do zero
  mantendo nomes, UV e sistema. **Samuel recusou em 09/11 23:32: corpo fica como está.**
- skin_vasco tem escudo/nome de clube real: não vai pro jogo.
