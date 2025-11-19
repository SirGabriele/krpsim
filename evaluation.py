from process import Process


def evaluation(stock: dict[str, int], processes: list[Process], optimize: str):
    if optimize in stock.keys() and stock[optimize] > 0:
        return stock[optimize] * 1000000

    #nombre d'actions

    #nombre de type ressource/total

    #