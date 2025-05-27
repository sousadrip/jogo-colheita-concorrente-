import threading
import time
import random
import sys
import os

NUM_ROBOS = 4
TEMPO_LIMITE_SEGUNDOS = 120
META_RECURSOS = 76

CAPACIDADE_CAMPO_CRISTAIS = 2
TEMPO_COLETA_CRISTAIS_MIN = 1
TEMPO_COLETA_CRISTAIS_MAX = 3

CAPACIDADE_CAMPO_BIOGEL = 1
TEMPO_COLETA_BIOGEL_MIN = 2
TEMPO_COLETA_BIOGEL_MAX = 4

TEMPO_MOVIMENTO_MIN = 0.5
TEMPO_MOVIMENTO_MAX = 1.5

class SiloCentral:
    def __init__(self):
        self.recursos_coletados = 0
        self.lock = threading.Lock()

    def depositar(self, quantidade, robo_id):
        with self.lock:
            self.recursos_coletados += quantidade
            print(f"[Robô {robo_id}] Depositou {quantidade} recurso(s). Total no Silo: {self.recursos_coletados}")
            return self.recursos_coletados

    def get_total_recursos(self):
        with self.lock:
            return self.recursos_coletados

class CampoColeta:
    def __init__(self, nome, capacidade, tempo_min, tempo_max):
        self.nome = nome
        self.semaforo = threading.Semaphore(capacidade)
        self.tempo_min = tempo_min
        self.tempo_max = tempo_max
        self.lock_print = threading.Lock()

    def entrar(self, robo_id):
        with self.lock_print:
            print(f"[Robô {robo_id}] Tentando entrar no {self.nome}...")
        self.semaforo.acquire()
        with self.lock_print:
            print(f"[Robô {robo_id}] Entrou no {self.nome}.")

    def sair(self, robo_id):
        self.semaforo.release()
        with self.lock_print:
            print(f"[Robô {robo_id}] Saiu do {self.nome}.")

    def coletar(self, robo_id):
        tempo_coleta = random.uniform(self.tempo_min, self.tempo_max)
        with self.lock_print:
            print(f"[Robô {robo_id}] Coletando no {self.nome} por {tempo_coleta:.1f}s...")
        time.sleep(tempo_coleta)
        recursos_coletados = 1 
        with self.lock_print:
             print(f"[Robô {robo_id}] Coletou {recursos_coletados} recurso(s) no {self.nome}.")
        return recursos_coletados


class RoboColetor(threading.Thread):
    def __init__(self, id, silo, campos_coleta, evento_parada):
        threading.Thread.__init__(self)
        self.id = id
        self.silo = silo
        self.campos_coleta = campos_coleta
        self.evento_parada = evento_parada
        self.recursos_carregados = 0

    def mover_para(self, destino):
        tempo_movimento = random.uniform(TEMPO_MOVIMENTO_MIN, TEMPO_MOVIMENTO_MAX)
        time.sleep(tempo_movimento)

    def run(self):
        print(f"[Robô {self.id}] Iniciando operações.")
        while not self.evento_parada.is_set():
            try:
                campo_escolhido = random.choice(self.campos_coleta)

                self.mover_para(campo_escolhido.nome)
                if self.evento_parada.is_set(): break

                campo_escolhido.entrar(self.id)
                if self.evento_parada.is_set():
                    campo_escolhido.sair(self.id)
                    break

                try:
                    self.recursos_carregados = campo_escolhido.coletar(self.id)
                finally:

                    campo_escolhido.sair(self.id)

                if self.evento_parada.is_set(): break

                self.mover_para("Silo Central")
                if self.evento_parada.is_set(): break

                total_atual = self.silo.depositar(self.recursos_carregados, self.id)
                self.recursos_carregados = 0

                time.sleep(random.uniform(0.1, 0.5))

            except Exception as e:
                print(f"[Robô {self.id}] Erro inesperado: {e}")
                break

        print(f"[Robô {self.id}] Encerrando operações.")

def limpar_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def exibir_status(tempo_decorrido, silo):
    limpar_terminal()
    print("--- Fazenda Cósmica: Colheita Concorrente ---")
    print(f"Tempo Decorrido: {int(tempo_decorrido)}s / {TEMPO_LIMITE_SEGUNDOS}s")
    recursos_atuais = silo.get_total_recursos()
    print(f"Recursos no Silo: {recursos_atuais} / {META_RECURSOS}")
    print("---------------------------------------------")

    progresso = int((recursos_atuais / META_RECURSOS) * 20) if META_RECURSOS > 0 else 0
    barra = '[' + '#' * progresso + '-' * (20 - progresso) + ']'
    print(f"Progresso Meta: {barra}")
    print("---------------------------------------------")
    print("Log de Atividades (últimas mensagens):")

def main():
    silo = SiloCentral()
    campo_cristais = CampoColeta("Campo de Cristais Azuis", CAPACIDADE_CAMPO_CRISTAIS, TEMPO_COLETA_CRISTAIS_MIN, TEMPO_COLETA_CRISTAIS_MAX)
    campo_biogel = CampoColeta("Fonte de Bio-gel Verde", CAPACIDADE_CAMPO_BIOGEL, TEMPO_COLETA_BIOGEL_MIN, TEMPO_COLETA_BIOGEL_MAX)
    campos = [campo_cristais, campo_biogel]

    robos = []
    evento_parada = threading.Event()

    print("Iniciando simulação da Fazenda Cósmica...")
    time.sleep(2)

    for i in range(NUM_ROBOS):
        robo = RoboColetor(i + 1, silo, campos, evento_parada)
        robos.append(robo)
        robo.start()

    inicio_tempo = time.time()
    tempo_decorrido = 0

    try:
        while tempo_decorrido < TEMPO_LIMITE_SEGUNDOS:
            tempo_decorrido = time.time() - inicio_tempo
            exibir_status(tempo_decorrido, silo)

            if silo.get_total_recursos() >= META_RECURSOS:
                print("\n*** VITÓRIA! Meta de recursos atingida! ***")
                break

            time.sleep(1)
        else:
            exibir_status(tempo_decorrido, silo)
            print("\n--- DERROTA! Tempo esgotado! ---")

    except KeyboardInterrupt:
        print("\nInterrupção manual detectada. Encerrando...")
    finally:
        print("Enviando sinal de parada para os robôs...")
        evento_parada.set()

        print("Aguardando robôs finalizarem...")
        for robo in robos:
            robo.join()

        print("\n--- Simulação Encerrada ---")
        print(f"Total de Recursos Coletados: {silo.get_total_recursos()}")
        print("---------------------------")

if __name__ == "__main__":
    main()