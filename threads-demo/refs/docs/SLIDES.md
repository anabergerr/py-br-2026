# Estrutura da Palestra: Do Conceito ao Código

## Tópico 1: O que é Thread?
- **Definição simples:** É a menor unidade de execução de um programa.
- **Múltiplas threads:** Em vez de fazer uma tarefa por vez do início ao fim, criamos várias "linhas de trabalho" no mesmo programa.
- **O benefício direto:** Elas compartilham a mesma memória (as mesmas variáveis e dados), o que facilita a comunicação entre elas.

## Tópico 2: Concorrência vs. Paralelismo em Múltiplas Threads
- **O ponto central:** Ter múltiplas threads não significa automaticamente que elas rodam ao mesmo tempo. Depende de como a CPU as executa.
- **Concorrência (Lidar com várias coisas ao mesmo tempo):**
  - As threads alternam a execução tão rápido que parece tudo simultâneo.
  - Ocorre mesmo em processadores de 1 único núcleo.
  - **Analogia do Restaurante:** 1 garçom atendendo 4 mesas. Ele anota o pedido da mesa 1, corre pra levar a conta da mesa 2, traz a bebida da mesa 3. Ele lida com todas as mesas, mas só faz uma ação por vez.
- **Paralelismo (Fazer várias coisas no mesmo milissegundo):**
  - Cada thread roda em um núcleo físico diferente da CPU.
  - Exige processadores multi-core.
  - **Analogia do Restaurante:** 4 garçons para 4 mesas. Cada garçom atende sua mesa de forma totalmente independente e ao mesmo tempo.

## Tópico 3: Onde entra o GIL no Python?
- **O papel do GIL:** O Global Interpreter Lock é uma trava interna do CPython que permite apenas 1 thread executar bytecode Python por vez.
- **O impacto prático:**
  - **Para I/O (Web, Banco de Dados, Arquivos):** O Python entrega concorrência. Quando uma thread fica esperando a resposta de uma requisição, ela libera o GIL para outra thread trabalhar.
  - **Para CPU-Bound (Cálculos pesados):** O GIL impede o paralelismo real. Mesmo com 16 núcleos no seu processador, o Python tradicional vai usar apenas 1 núcleo, alternando entre as threads.

## Tópico 4: A Revolução do Free-threaded Python (PEP 703)
- **O fim da limitação:** O Python 3.13+ introduziu a opção de remover o GIL (`python3