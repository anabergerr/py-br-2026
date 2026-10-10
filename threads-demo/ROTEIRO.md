# Roteiro de fala

Acompanha o `index.html`, na ordem. Setas ou espaço trocam o slide. O parágrafo é o que falar. O que está em **Ao vivo** é terminal — pode pular se o tempo apertar. A tabela do final já tem uma medição pronta.

Antes de subir: `index.html` aberto, e dois terminais na pasta `threads-demo`.

```powershell
.\.venv\Scripts\Activate.ps1
.\.venv-ft\Scripts\python.exe -c "import sys; print(sys._is_gil_enabled())"
```

O segundo tem que imprimir `False`.

---

## 1 — Capa

Abre com o gancho da tela, no ritmo de quem conta um segredo: você joga mais threads no problema, e às vezes o programa voa, às vezes não muda nada. Pausa. A palestra inteira é sobre esse "às vezes" — quando thread ajuda e quando é só ilusão.

Dois exemplos vão responder isso. Uma planilha de CEPs, que passa o tempo esperando a internet. E um carimbo de arquivo, que só usa CPU. No meio, o GIL.

## 2 — O que é thread

Thread é a menor unidade de execução de um programa. É uma linha de trabalho, e ela faz uma ação por vez.

O exemplo da palestra: a planilha tem uma linha por cliente, e a ação é buscar o endereço daquele CEP. Uma thread pega um CEP, busca, e já pode pegar o próximo. Várias threads são várias dessas linhas de trabalho ao mesmo tempo. Todas estão no mesmo programa e enxergam a mesma lista, então uma pode guardar o endereço na linha que a outra acabou de ler.

A última frase do slide fica em aberto: ter várias linhas não significa que elas rodam juntas. Pra responder isso, faltam dois nomes em volta da thread.

## 3 — Do programa até a CPU

A ação do slide anterior mora dentro de um processo. O processo é o programa inteiro: o script que abre a planilha e percorre as linhas. Buscar um CEP é uma ação dentro dele. Outro processo é outra cópia desse script, com outra lista. Uma cópia não vê a lista da outra.

Dentro desse processo, cada thread é uma linha de trabalho. Uma busca o CEP da linha 1, outra busca o da linha 2. Lá na frente, a ação vira carimbar um bloco. Elas dividem a mesma planilha. A comunicação é direta por causa disso.

O núcleo é a CPU que executa a ação. Não é a linha da planilha. É o hardware que faz a consulta rodar.

A frase de baixo monta a pergunta. Imagina que a gente resolve buscar 4 linhas da planilha de uma vez, em vez de uma. São 4 threads, 4 buscas de CEP, todas dentro de um processo só: o script da planilha. O 4 é só pra caber no desenho — podia ser 2 ou 20.

Agora a pergunta: quantos núcleos executam essas 4 threads? Um núcleo executa uma thread por instante. Se a máquina tiver 4 núcleos livres, dá pra executar as 4 juntas. Os próximos dois slides são essas duas respostas. O processo é o mesmo nos dois, o restaurante. O que muda é quantos garçons atendem as mesas.

## 4 — Concorrência

Este é o caso de um núcleo. Quatro threads, quatro CEPs, um processo. O garçom é o núcleo. Cada mesa é uma busca. Ele atende uma, larga, atende a outra. As quatro estão em andamento, e neste instante só uma está sendo executada. O nome disso é concorrência: várias threads, o núcleo revezando.

## 5 — Paralelismo

Este é o outro caso. Quatro núcleos, quatro garçons, cada um executa uma thread agora. O nome disso é paralelismo: uma thread em cada núcleo, as quatro buscas neste instante.

Continua sendo um processo só, o mesmo restaurante, a mesma planilha. A diferença não é a thread nem o processo. É quantos núcleos estão executando. Guarde a palavra processo: ela volta como solução lá na frente, quando o Python não conseguir usar mais de um núcleo sozinho.

## 6 — GIL

Aqui vem a reviravolta. Lembra dos quatro garçons do slide anterior, o paralelismo bonito? Em Python puro, isso não acontece. O motivo tem nome: GIL, uma trava do CPython. Só uma thread executa código Python por vez. As outras esperam a vez.

Por causa dessa trava, o Python recusa o desenho dos quatro garçons. A máquina pode ter oito núcleos. Nesse processo, as threads voltam para o garçom único, revezando. Os outros núcleos ficam ociosos. Deixa essa decepção no ar — o próximo slide mostra quando ela não importa.

## 7 — Quando a thread ajuda?

Se o GIL segura um núcleo, a pergunta seguinte é quando a thread ainda vale a pena. Depende de onde o tempo some.

Se o programa está parado esperando rede, disco ou API, o trabalho é I/O-bound. O exemplo é a consulta no ViaCEP. As esperas se juntam, então threads ajudam. O caminho usual é `ThreadPoolExecutor` ou asyncio.

Se o programa está calculando na máquina, é CPU-bound. O exemplo é carimbar um arquivo. O GIL fica preso na conta, então threads não ajudam. O caminho usual é processo, código nativo, ou o Python free-threaded.

A gente entra agora pela coluna da esquerda. A coluna da direita volta depois do ViaCEP.

## 8 — A planilha

Conta como cena: caiu no seu colo uma planilha com milhares de clientes, cada linha com um CEP, e você precisa da rua, do bairro e da cidade de todas. Cada linha é uma ação: buscar aquele CEP numa chamada HTTPS de verdade na API do ViaCEP. Não tem `sleep` no lugar da rede. Uma linha não depende da outra. Uma por vez, o tempo total vira a soma de todas as esperas. É o garçom único, uma ação depois da outra.

## 9 — Uma por vez

O laço é esse garçom, uma ação por vez. Para cada linha, `lookup_cep`. A função manda o HTTPS e fica parada até o JSON voltar. A próxima ação espera a anterior terminar.

**Ao vivo**

```powershell
python src/main.py sequencial --limit 20
```

No log: `Iniciando`, `Finalizando`, `Iniciando`, `Finalizando`. Nunca dois `Iniciando` seguidos. O tempo total fica no final.

## 10 — Várias chamadas em voo

O mesmo trabalho, agora com várias threads. `ThreadPoolExecutor` com 10 workers, e o `map` entrega cada linha para `_lookup`. Cada worker pega uma ação: um CEP. Dez workers e vinte linhas são dez threads dentro de um processo. Quando uma termina, ela pega a próxima. O `map` devolve o resultado na ordem do CSV. O log segue a ordem em que a resposta chega.

**Ao vivo**

```powershell
python src/main.py threads --limit 20 --workers 10
```

Aqui aparecem vários `Iniciando` antes do primeiro `Finalizando`. `worker_0`, `worker_1`: cada um pegou uma linha. Compara o tempo total com o do slide anterior.

## 11 — O tempo encolhe

Em cima está o laço: uma espera atrás da outra. Embaixo, as quatro chamadas viajam juntas. O de baixo termina perto da chamada mais lenta do grupo, mais um pouco de overhead. Parece o desenho dos quatro garçons. O próximo slide explica por que ainda é o garçom único.

## 12 — Por que o ViaCEP acelera

Enquanto a thread espera a internet, ela solta o GIL. Outra thread entra e dispara a próxima chamada. A rede fica ocupada junta. O Python segue revezando um núcleo só. O GIL continua ali. Ele só não segura a thread durante a espera.

O tempo encolheu porque as esperas se cruzaram. Continua sendo o um garçom: o Python reveza um núcleo, e quem anda junto é a rede.

## 13 — Carimbo

Faz a pergunta da tela antes de virar: e se não houver espera nenhuma? No ViaCEP a thread ganhava tempo porque ficava parada esperando a rede. Tira a espera. A ação trocou: em vez de buscar um CEP, cada thread carimba um bloco. A CPU trabalha o tempo inteiro, então o GIL não tem hora de soltar.

O trabalho é um carimbo de arquivo. O nome é SHA-256. Você entrega um conteúdo e recebe um código curto. O mesmo conteúdo, o mesmo código. Mudou um byte, o carimbo muda. Na vida real, serve para saber se um arquivo chegou inteiro.

Aqui a gente não confere arquivo de verdade. O `hash_blocks` carimba centenas de milhares de bloquinhos de 1024 bytes. O tamanho é de propósito: o `hashlib` só solta o GIL a partir de 2048 bytes. Abaixo disso, a trava fica presa na conta.

## 14 — Um núcleo, ou vários

Nesse carimbo, com o GIL ligado, o `ThreadPoolExecutor` é o um garçom. Várias threads, um processo, um GIL. Elas se revezam no mesmo núcleo. O tempo empata com o sequencial.

O `ProcessPoolExecutor` são os quatro garçons. Cada worker é outro processo, com seu Python e seu GIL. Quatro workers podem ocupar quatro núcleos ao mesmo tempo. Aí o ganho aparece.

**Ao vivo, no Python com GIL**

```powershell
.\.venv\Scripts\python.exe src\main.py cpu --upto 800000 --workers 4
```

A primeira linha diz que o GIL está ligado. A leitura no final: threads perto de 1x, processos na frente.

## 15 — Sem o GIL

Gancho da tela: e se tirassem a trava? O slide anterior precisou de processo para ganhar núcleo, driblando o GIL por fora. E se a gente pudesse tirar o GIL por dentro? Desde o 3.13 existe um build oficial sem a trava: `python3.13t`, free-threaded, ainda experimental. É o mesmo `ThreadPoolExecutor` e o mesmo `hash_blocks`. Sem o GIL, aquelas threads deixam de ser o garçom único e passam a ocupar vários núcleos.

Bibliotecas em C podem quebrar nesse build. Essa demo usa só a biblioteca padrão. A checagem é `sys._is_gil_enabled()`, e aqui ela devolve `False`.

**Ao vivo, no free-threaded**

```powershell
.\.venv-ft\Scripts\python.exe src\main.py cpu --upto 800000 --workers 4
```

Mesmo comando do slide anterior. Desta vez as threads aceleram.

## 16 — Medido nesta máquina

Os dois slides anteriores, medidos. O mesmo carimbo, dois Pythons. Se o ao vivo ainda estiver rodando, esta tabela é uma medição já feita. O número mexe a cada execução. O padrão é o que importa.

Com o GIL ligado: sequencial 2,44s. Threads 2,60s, 0,94x — um núcleo só, e o overhead até deixa um pouco mais lento. Processos 1,32s, 1,85x.

Sem o GIL: o sequencial sobe para 3,17s. Esse build tem um custo. As threads caem para 1,11s, 2,87x. Processos 1,62s, 1,95x.

Com GIL, threads num núcleo só. Sem GIL, o ThreadPool ocupa vários núcleos.

## 17 — Três ideias

Fecha o caminho inteiro.

I/O-bound, a planilha: threads já ajudam hoje, porque a espera solta o GIL. É o um garçom, com a rede andando junta.

CPU-bound com GIL, o carimbo: o ThreadPool fica num núcleo só. Quem usa os outros núcleos é o processo, um garçom por núcleo.

Free-threaded: o mesmo ThreadPool finalmente ocupa vários núcleos.

Fecha com a regra de bolso da tela, que responde a pergunta mais comum — "então minhas threads rodam em núcleos diferentes?". Com o GIL, não: thread não espalha em núcleos, quem espalha é processo. Sem o GIL, sim, a thread também espalha. E cuidado com uma pegadinha: no I/O a thread acelera sem espalhar em núcleo nenhum — ali o ganho é a espera de rede se sobrepondo, não núcleo extra.

## 18 — Perguntas

O código está no repositório. A parte de CEP é o ViaCEP. A parte de CPU é o comando `cpu`. A comparação é a pasta `.venv` contra a `.venv-ft`.

---

## Se sobrar tempo

Os dois tempos do ViaCEP e o speedup, numa execução só:

```powershell
python src/main.py comparar --limit 20 --workers 10
```

Uma chamada só, para mostrar o endereço voltando:

```powershell
python src/main.py uma
```

## Se a rede falhar

O `cpu` não depende do ViaCEP. Segue do slide 13. A tabela do slide 16 fecha o argumento sem chamar a API.
