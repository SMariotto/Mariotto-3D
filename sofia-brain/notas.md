# Notas

- (2026-11-09) Lista FINAL de cabelos do skin-system (confirmada pelo Samuel, fazer depois): 1 liso repartido,
  2 jogador com degradê, 3 raspado, 4 cacheado curto, 5 crespo curto, 6 espetado com gel, 7 mullet (novo).
  Todos originais. Programa de desenho: tanto faz pra ele (sugerir Photopea/Krita/Aseprite).

- (2026-11-08) Sistema Sofia criado. Gatilho: "Sofia, ligar" no início da conversa. Sugestão de encerramento:
  "Sofia, desligar" (Sofia grava o resumo da sessão antes de terminar).
- (2026-11-08) Detalhes técnicos úteis: no Blender headless, `import bmesh` só funciona depois de `import bpy`;
  para gravar caminhos `//textures/...` use `relative_remap=False` ao salvar.
- (2026-11-09) Instalar Blender na nuvem: `pip install bpy==5.2.3` fica lentíssimo (~25 KB/s). Funciona baixar o .whl
  com curl em ~40 partes paralelas (`curl -r inicio-fim`) direto de files.pythonhosted.org, juntar e `pip install` o
  arquivo (~7 min). Conferir o sha256 com o da PyPI.
- (2026-11-09) Render de conferência com Cycles CPU (Workbench não mostra bem a transparência da camada do rosto).
