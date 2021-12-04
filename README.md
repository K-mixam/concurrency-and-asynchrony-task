# concurrency-and-asynchrony-task

<h2>IO-bound</h2>
Суть задания - посетить 100 случайных страниц в Википедии и сохранить все ссылки с этих страниц. Затем проанализировать скорость их обработки, используя ThreadPoolExecutor.

Этим кодом запишем все ссылки в файл res.txt:

    from urllib.request import urlopen
    from urllib.parse import unquote
    from bs4 import BeautifulSoup
    from tqdm import tqdm
    
    url = 'https://ru.wikipedia.org/wiki/%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F:%D0%A1%D0%BB%D1%83%D1%87%D0%B0%D0%B9%D0%BD%D0%B0%D1%8F_%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0'
    
    res = open('res.txt', 'w', encoding='utf8')
    
    for i in tqdm(range(100)):
        html = urlopen(url).read().decode('utf8')
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a')

        for l in links:
            href = l.get('href')
            if href and href.startswith('http') and 'wiki' not in href:
                print(href, file=res)

Всего получилось 786 ссылок

![Screenshot](screenshots_for_IO-bound/res_screenshot.png)

На протяжении работы программы количество используемой памяти почти не изменялось, а нагрузка на проессор находилась в районе 60%, периодически улетая в 98-100%. В конце (график ЦП) отчетливо видно момент, когда программа завершила работу:

![Screenshot](screenshots_for_IO-bound/task_manager_screenshot.png)

Всего на обработку одним потоком 786 ссылок ушло 1242 секунды:

![Screenshot](screenshots_for_IO-bound/one_thread_solution.png)

Теперь перепишем код, используя ThreadPoolExecutor:

    import concurrent.futures
    import urllib
    from urllib.request import urlopen, Request
    
    links = open('res.txt', encoding='utf8').read().split('\n')
    
    
    def load_url(url, timeout):
        with urllib.request.urlopen(url, timeout=timeout) as conn:
            return conn.read()
    
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(load_url, url, 60): url for url in links}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                request = Request(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 9.0; Win65; x64; rv:97.0) Gecko/20105107 Firefox/92.0'},
                )
            except Exception as exc:
                print(url, exc)
            else:
                print(url)

И теперь сравним время работы и нагрузку на ЦП одного потока с временем работы с 5, 10, 100 workers:

<h4>С max_workers=5:</h4>

![Sreenshot](screenshots_for_IO-bound/task_manager_screenshot_5-workers.png)
![Sreenshot](screenshots_for_IO-bound/5_threads_solution.png)

<h4>C max_workers=10:</h4>

![Sreenshot](screenshots_for_IO-bound/task_manager_screenshot_10-workers.png)
![Sreenshot](screenshots_for_IO-bound/10_threads_solution.png)
![Sreenshot](screenshots_for_IO-bound/10_threads_solution_first-seconds.png)
На диаграмме диспетчера (график ЦП) тест начинается примерно в середине (после проседания),его и стоит анализировать. 
На 3м скриншоте видны задержки первые 5.5 секунд в MainThread

<h4>И с max_workers=100:</h4>

![Sreenshot](screenshots_for_IO-bound/task_manager_screenshot_100-workers.png)
![Sreenshot](screenshots_for_IO-bound/100_threads_solution.png)
![Sreenshot](screenshots_for_IO-bound/100_threads_solution_first-seconds.png)
На 3м скриншоте также видны задержки в MainThread, но уже в течение 8 секунд.
Всего ушло 218 секунд (на скриншоте может быть плохо видно)

В итоге по графикам видно, что количество потоков в IO-bound задаче никак не влияет на количество используемой памяти. Нагрузка на процессор при max_workers=5 не сильно отличается от нагрузки при max_workers=100, т.е. использование ThreadPoolExecutor увеличивает нагрузку на процессор, но предельное значение уровня нагрузки достигается почти сразу и дальнейшее увеличение количества воркеров ведет только к изменению времени.<br>

Теперь о времени. Для 5, 10 и 100 воркеров время работы составило 535, 292 и 218 секунд соответственно. Значит увеличение количества потоков ведет к увеличению скорости работы, но постепенно увеличение количества потоков будет приводить ко все меньшему увеличению производительности, пока не будет достигнут предел.

_____
<<<<<<< HEAD

<h2>CPU-bound</h2>

Теперь генерируем монетки. Программа будет работать, пока не найдет 4 монетки. Начинаем с генерации на одном ядре:

    from hashlib import md5
    from random import choice
    
    coins = 0
    while coins != 4:
        s = "".join([choice("0123456789") for i in range(50)])
        h = md5(s.encode('utf8')).hexdigest()
    
        if h.endswith("00000"):
            coins += 1
            print(s, h)

Результат работы программы:

![Screenshot](screenshots_for_CPU-bound/task-manager-one-core.png)
![Scrreenshot](screenshots_for_CPU-bound/one-core-solution.png)


Теперь перепишем код с использованием ProcessPoolExecutor:

    from hashlib import md5
    from random import choice
    import concurrent.futures
    
    
    def crypt_miner(i):
        while True:
            s = "".join([choice("0123456789") for j in range(50)])
            h = md5(s.encode('utf8')).hexdigest()
    
            if h.endswith("00000"):
                return f"{s} {h}"
    
    
    def main():
        with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
            for coin in executor.map(crypt_miner, range(4)):
                print(coin)
    
    
    if __name__ == '__main__':
        main()

Для анализа тестов важно знать информацию о процессоре (2 ядра):

![Screenshot](screenshots_for_CPU-bound/processor_info.png)

Тесты начнем с <h4>max_workers=2:</h4>

![Screenshot](screenshots_for_CPU-bound/task-manager_2-workers_start.png)
С самого начала процессор был нагружен на 100%, диспетчер отображал 2 запущенных процесса

![Screenshot](screenshots_for_CPU-bound/task-manager_2-workers_end.png)
Уровень загруженности процесора не менялся до конца работы программы

![Screenshot](screenshots_for_CPU-bound/2-cores-solution.png)
Обратил внимание на то,что в консоли монеты появлялись парами. Не знаю, влияло ли это как-нибудь на скорость вычислений, но время работы даже больше, чем без ProcessPoolExecutor

<h4>Теперь max_workers=4:</h4>

![Screenshot](screenshots_for_CPU-bound/task-manager_4-workers_start.png)
Нагрузка также с самого начала 100%, диспетчер отображает 4 запущенных процесса

![Screenshot](screenshots_for_CPU-bound/task-manager_4-workers_end.png)
И как в прошлый раз, нагрузка оставалсь 100% до конца работы программы

![Screenshot](screenshots_for_CPU-bound/4-cores-solution.png)
Но время изменилось, монетки майнились быстрее


На этапе <h4>max-workers=10</h4> я не могу объяснить происходящее:

![Screenshot](screenshots_for_CPU-bound/task-manager_10-workers_start.png)
Началось все так же со 100%, но диспетчер отображал уже только 4 процесса, которые занимали основные ресуры процессора(23-24% на каждый процесс)

![Screenshot](screenshots_for_CPU-bound/task-manager_10-workers_end.png)
Затем уровень нагрузки упал. Я не сделал скрины, но осталось только 2 процесса, которые делили ресурсы уже по 46-48%. При этом в консоли не было ни одной монетки. Под конец остался один процесс, а затем программа заврешила работу

![Screenshot](screenshots_for_CPU-bound/10-cores-solution.png)
Время майнинга сопоставимо с временем при 4 ворекерах. 


И последний тест с <h4>max-workers=100:</h4>

![Screenshot](screenshots_for_CPU-bound/task-manager_100-workers_start.png)
Как и раньше сразу 100% нагрузка и 4 процесса

![Screenshot](screenshots_for_CPU-bound/task-manager_100-workers_middle.png)
Вот осталось 3 процесса при той же нагрузке в 100%. Если я правильно понял, процесс заканчивается, когда сгенерирована монетка, но при этом в консоль монетки выводятся только парами

![Screenshot](screenshots_for_CPU-bound/task-manager_10-workers_end.png)
Последняя монетка создана, все процессы отработали

![Screenshot](screenshots_for_CPU-bound/100-cores-solution.png)
Монетки майнились на компьютере с ОС Linux, поэтому ограничение на максимальное количество воркеров 61 (такое стоит на винде) здесь не сработало, но это самое было самое долгое выполнение программы
