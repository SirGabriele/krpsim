from __future__ import annotations

import heapq
import logging
import random
from math import inf

from kr_config import MAX_WEIGHT, MAX_CYCLE_PER_MANAGER
from process import Process
from stock import Stock
from utils.is_time_up import is_time_up

logger = logging.getLogger()


class Manager:
    def __init__(self,
                 manager_id: int,
                 gen_id: int,
                 stock: Stock,
                 processes: list[Process],
                 resources: set[str],
                 resources_heatmap: dict[str, float],
                 end_timestamp: float,
                 weights: dict[str, float] | None = None
                 ):
        self.id = manager_id
        self.gen_id = gen_id
        self.processes = processes
        self.resources = resources
        self.resources_heatmap = resources_heatmap
        self.stock = stock.clone()
        self.weights = self.__create_weights(weights)
        self.end_timestamp = end_timestamp
        self.current_delay = 0
        self.processes_in_progress = []
        self.score = 0
        self.cycle = 0
        self.nb_completed_processes = 0
        self.print_trace = False
        self.__mutate()

    def __create_weights(self, weights: dict[str, float]) -> dict[str, float]:
        weights = (
            {resource: random.randint(0, MAX_WEIGHT) for resource in self.resources}
            if weights is None
            else weights.copy()
        )
        for resource_to_optimize in self.stock.resources_to_optimize:
            if not resource_to_optimize == "time":
                weights[resource_to_optimize] = MAX_WEIGHT * 1000
        return weights

    def reset(self, stock: Stock, end_timestamp: float) -> None:
        """
        Resets the manager's state to erase its previous execution.
        :return: None
        """
        self.stock = stock.clone()
        self.score = 0
        self.cycle = 0
        self.nb_completed_processes = 0
        self.processes_in_progress = []
        self.end_timestamp = end_timestamp

    def run(self, print_trace: bool = False) -> None:
        """
        Starts the manager's lifecycle. It lasts as long as it does not reach the maximum allowed actions or maximum allowed cycles
        and that time is not up.
        :return: None
        """
        logger.info("Generation [{}] - Manager [{}] - Starting simulation".format(self.gen_id, self.id))
        self.print_trace = print_trace
        self.current_delay = 0
        while self.current_delay < MAX_CYCLE_PER_MANAGER:

            # --- A. SÉCURITÉ RÉELLE ---
            # Si le programme tourne depuis 10 secondes (temps réel), on coupe tout.
            if is_time_up(self.end_timestamp):
                break

            # --- B. RÉCOLTE (Harvest) ---
            # On regarde le tas : Est-ce qu'il y a des process finis maintenant (ou avant) ?
            while self.processes_in_progress and self.processes_in_progress[0][0] <= self.current_delay:
                end_time, _, process = heapq.heappop(self.processes_in_progress)
                # On encaisse les gains
                if process.outputs:
                    for res, qty in process.outputs.items():
                        self.stock.add(res, qty)

                self.nb_completed_processes += 1

            # --- C. LANCEMENT (Decision) ---
            # Avec les nouveaux stocks, on lance tout ce qu'on peut
            while True:
                # La méthode fait tout : recherche, choix et lancement
                did_launch = self.__find_and_launch_best_process()

                if did_launch:
                    did_launch_something = True
                else:
                    break  # Plus rien à lancer

            # --- D. SAUT TEMPOREL (Le Kangourou) ---

            # S'il n'y a plus aucun processus en cours...
            if not self.processes_in_progress:
                # ... et qu'on n'a rien lancé de nouveau à l'étape C
                # Alors on est bloqué ou on a fini. On arrête la simulation.
                break

            # On regarde quelle est la prochaine échéance dans le futur
            if not self.processes_in_progress:
                break
            next_wakeup_time = self.processes_in_progress[0][0]

            # SAUT ! On met à jour l'heure virtuelle.
            # Si le prochain événement est plus tard, on avance d'un coup.
            if next_wakeup_time > self.current_delay:
                self.current_delay = next_wakeup_time
            else:
                # Cas rare : Si un process a duré 0 cycle, on est déjà à la bonne heure.
                # On boucle juste pour le récolter à l'étape B.
                pass

            # Simulation terminée : On calcule le score
        self.__evaluate()

    def __score_process(self, process: Process) -> float:
        expenses = 0
        if process.inputs is not None:
            for input_resource, input_quantity in process.inputs.items():
                expenses += self.weights.get(input_resource, 0) * input_quantity
        income = 0
        if process.outputs is not None:
            for output_resource, output_quantity in process.outputs.items():
                income += self.weights.get(output_resource, 0) * output_quantity
        delay = process.delay if process.delay > 0 else 1
        return (income - expenses) / delay

    def __find_and_launch_best_process(self) -> bool:
        """
        Cherche le meilleur process et le lance directement.
        Retourne True si on a lancé un truc, False sinon.
        """
        best_process = None
        best_score = -inf  # Ou -infinity si tu acceptes les scores négatifs

        # On parcourt TOUS les process une seule fois
        for process in self.processes:

            # 1. Check rapide : Stocks suffisants ?
            # (Optimisation: coder can_launch_process inline pour éviter l'appel de fonction)
            if not self.stock.can_launch_process(process):
                continue

            # 2. Check rapide : Temps virtuel
            if self.current_delay + process.delay > MAX_CYCLE_PER_MANAGER:
                continue

            # 3. Calcul du Score
            # (Appel direct à ta logique de score dynamique)
            score = self.__score_process(process)

            # 4. Compétition
            if score > best_score:
                best_score = score
                best_process = process

        # Si on a trouvé un gagnant
        if best_process:
            self.__launch_process(best_process)
            return True

        return False

    def __get_launchable_processes(self) -> list[Process]:
        """
        Returns a list of processes that can be launched, aka processes the inputs of which are in stock.
        :return: list
        """
        return [process for process in self.processes if self.stock.can_launch_process(process)]

    def __launch_process(self, process: Process) -> None:
        """
        Launches a single process. Adds the process to the list of processes in progress.
        If the process has inputs, subtracts them from the stock.
        :return: None
        """
        if process.inputs:
            for res, qty in process.inputs.items():
                self.stock.consume(res, qty)
        finish_time = self.current_delay + process.delay
        heapq.heappush(self.processes_in_progress, (finish_time, id(process), process))
        # logger.debug("Generation [{}] - Manager [{}] - Launch process '{}'".format(self.gen_id, self.id, process.name))
        if self.print_trace:
            print(f"{self.current_delay}:{process.name}")

    def __evaluate(self) -> None:
        """
        Evaluates the manager's score for this generation.
        :return: None
        """
        if self.current_delay == 0:
            self.score = 1
            return
        self.score = 1
        inventory_value = 0.0
        for resource_name, quantity in self.stock.inventory.items():
            if quantity > 0:
                unit_value = self.resources_heatmap.get(resource_name, 0.0)
                inventory_value += quantity * unit_value
        self.score = (inventory_value * 1000) - self.current_delay

    def __reverse_weights(self) -> None:
        active_keys = [k for k in self.weights if k not in self.stock.resources_to_optimize]
        sorted_keys = sorted(active_keys, key=self.weights.get)

        active_values = [self.weights[k] for k in active_keys]
        reversed_values = sorted(active_values, reverse=True)

        result = self.weights.copy()

        for key, new_value in zip(sorted_keys, reversed_values):
            result[key] = new_value
        self.weights = result

    def __mutate(self) -> None:
        """
        Performs mutation on the manager.
        :return: None
        """
        for resource in self.resources:
            if resource in self.stock.resources_to_optimize:
                continue
            if random.uniform(0, 1) >= 0.9:
                self.weights[resource] += random.uniform(-0.05 * MAX_WEIGHT, 0.05 * MAX_WEIGHT)
                self.weights[resource] = max(min(self.weights[resource], 0), MAX_WEIGHT)
            if random.uniform(0, 1) >= 0.95:
                self.weights[resource] += random.uniform(-0.2 * MAX_WEIGHT, 0.2 * MAX_WEIGHT)
                self.weights[resource] = max(min(self.weights[resource], 0), MAX_WEIGHT)
        if random.uniform(0, 1) >= 0.99:
            self.__reverse_weights()
