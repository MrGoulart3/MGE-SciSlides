# Guia de design para slides científicos

[Read in English](GUIDE.md)

Regras destiladas da construção e revisão de uma palestra real para calouros. Cada regra é
barata de seguir e cara de ignorar. O kit cobra as mecânicas (`scislides-check`); o resto é
julgamento.

## Conteúdo

1. **Uma ideia por slide.** Se o título precisa de "e", você precisa de dois slides.
2. **Títulos-afirmação.** "A energia livre conta a história que a entalpia sozinha não conta"
   vale mais que "Perfil de energia". O título é a mensagem; a figura é a evidência.
3. **Público primeiro.** Para calouros: defina cada sigla uma vez, prefira o desenho da
   molécula ao nome, troque o jargão pelo que a coisa faz e comece com uma pergunta ou um
   objeto surpreendente, não com um índice.
4. **Número leva a fonte.** Coloque a origem numa linha pequena de rodapé (`source`):
   "Fonte: autor, ano" ou "cálculo próprio, método X". Número sem fonte é opinião.
5. **Credite toda imagem e vídeo** no slide em que aparece e mantenha um arquivo de
   proveniência (veja [MEDIA.md](MEDIA.md)).
6. **Notas do orador** guardam o que você vai dizer, a frase de transição e o tempo.
   Escreva ao montar o slide, não na véspera (`Deck.notes`).

## Tipografia e layout

7. **Tamanhos mínimos.** Texto 18 pt ou mais; legendas, créditos, fontes e sobretítulos
   14 pt; número de página 10 pt. `Deck.text` eleva tamanhos pequenos ao piso do tema e o
   verificador acusa qualquer coisa menor num deck existente.
8. **Três linhas valem mais que nove.** Se o texto estoura, corte palavras em vez de
   diminuir a fonte.
9. **Grade.** 13,333 x 7,5 pol, margens laterais de 0,75 pol, sobretítulo em y = 0,6,
   título em y = 1,11, conteúdo a partir de y = 2,4, rodapé perto de y = 6,7. Reusar a grade
   faz os slides parecerem parentes.
10. **Cor significa algo.** Um destaque para estrutura (sobretítulo, marcadores, progresso)
    e os outros dois para séries de dados. Nunca dependa só da cor: varie o estilo da linha e
    ponha rótulos.
11. **Contraste.** Os temas já trazem razões WCAG verificadas; ao criar o seu, chame
    `Theme.check()`.
12. **Texto alternativo** em toda imagem (`alt=` em `Deck.pic`); também documenta o slide.

## Navegação e ritmo

13. **Linha de progresso ("carrier").** Uma linha fina com N estações e um marcador mostra
    onde o público está (`Deck.carrier`). Use nos slides de conteúdo de palestras com mais de
    dez minutos.
14. **Revelações por clique.** Revele camadas, nomes ou etapas um por clique para controlar o
    ritmo (`layouts.layers_figure`, `layouts.names_reveal`). Diga a ideia primeiro, depois
    clique.
15. **Transições.** Fade entre seções, morph só quando dois slides compartilham objetos.
    Nada voa, gira ou quica.
16. **Aberturas de seção.** Uma imagem em sangria com o título num lado escuro
    (`layouts.opener`) recupera a atenção depois de uma parte densa.

## Processo

17. **Renderize e olhe antes de entregar.** `scislides-render deck.pptx` gera PNGs e uma folha
    de contato. Estouro de texto, fontes erradas e figuras cortadas só aparecem quando você
    olha. Fontes ausentes na máquina de renderização são substituídas; abra também o deck no
    computador da apresentação.
18. **Preserve o original.** Nunca edite o arquivo recebido. Trabalhe em cópias `v1`, `v2`,
    ... e escreva uma linha de registro de mudanças para cada. Os auxiliares de
    `scislides.edit` (reordenar, renumerar, trocar texto, trocar imagem no lugar) tornam
    pequenas revisões seguras.
19. **Verifique, depois entregue.** `scislides-check` para fontes, formas fora do slide,
    avisos de estouro, falta de texto alternativo e tamanho do arquivo; `--forbid` para
    caracteres que seu guia de estilo bane.
20. **Pese o arquivo.** Comprima fotos ao tamanho em que aparecem, converta clipes em GIFs
    curtos ou mantenha MP4 quando precisar de som, e defina um orçamento de tamanho (50 MB por
    padrão no verificador).
21. **Ensaie com o deck real** no projetor real ao menos uma vez; guarde um PDF de reserva.
