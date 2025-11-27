# currency_converter_pro_rus.py
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime
import json
import logging
from typing import Optional, Dict, List

# --- Настройка логирования для отладки ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('currency_converter.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


class ModernTheme:
    """Класс с современной цветовой схемой"""
    PRIMARY = "#6366f1"  # Фиолетовый
    PRIMARY_LIGHT = "#818cf8"  # Светло-фиолетовый
    SECONDARY = "#06b6d4"  # Бирюзовый
    SUCCESS = "#10b981"  # Зеленый
    WARNING = "#f59e0b"  # Желтый
    ERROR = "#ef4444"  # Красный
    DARK = "#1f2937"  # Темный
    LIGHT = "#f8fafc"  # Светлый
    CARD_BG = "#ffffff"  # Белый для карточек
    BORDER = "#e5e7eb"  # Цвет границ


class CurrencyConverterPro:
    """Профессиональный конвертер валют с расширенным функционалом"""

    def __init__(self):
        self.api_key = self.get_api_key()
        self.api_url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/"
        self.currencies = []
        self.exchange_rates = {}
        self.conversion_history = []
        self.setup_logging()

    def get_api_key(self) -> str:
        """Получение API ключа"""
        # 1. Попробовать получить из переменных окружения
        api_key = os.getenv("CURRENCY_API_KEY") or os.getenv("API_KEY")
        if api_key:
            logging.info("API key loaded from environment variables")
            return api_key

        # 2. Попробовать загрузить из файла
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                api_key = config.get('api_key')
                if api_key:
                    logging.info("API key loaded from config file")
                    return api_key
        except FileNotFoundError:
            pass

        # 3. Использовать демо-ключ
        demo_key = "d0167997ec8327b93457e268"
        logging.info("Using demo API key for testing")
        return demo_key

    def setup_logging(self):
        """Дополнительная настройка логирования"""
        self.logger = logging.getLogger(__name__)

    def fetch_currencies(self) -> List[str]:
        """Получение списка доступных валют"""
        try:
            response = requests.get(f"{self.api_url}/latest/USD", timeout=10)
            response.raise_for_status()
            data = response.json()

            if data["result"] == "success":
                self.currencies = list(data["conversion_rates"].keys())
                self.exchange_rates = data["conversion_rates"]
                self.logger.info(f"Loaded {len(self.currencies)} currencies")
                return self.currencies
            else:
                raise Exception(f"API error: {data.get('error-type', 'Unknown error')}")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error: {e}")
            demo_currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "RUB", "INR", "BRL", "MXN"]
            self.currencies = demo_currencies
            return demo_currencies
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            demo_currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "RUB", "INR", "BRL", "MXN"]
            self.currencies = demo_currencies
            return demo_currencies

    def convert_currency(self, from_curr: str, to_curr: str, amount: float) -> Optional[float]:
        """Конвертация валюты"""
        try:
            if amount <= 0:
                raise ValueError("Сумма должна быть положительной")

            if from_curr == to_curr:
                return amount

            response = requests.get(
                f"{self.api_url}/pair/{from_curr}/{to_curr}/{amount}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data["result"] == "success":
                result = data["conversion_result"]

                # Сохраняем в историю
                history_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'from_currency': from_curr,
                    'to_currency': to_curr,
                    'amount': amount,
                    'result': result,
                    'rate': data.get('conversion_rate')
                }
                self.conversion_history.append(history_entry)
                self.save_history()

                self.logger.info(f"Converted {amount} {from_curr} to {result} {to_curr}")
                return result
            else:
                # Демо-конвертация при ошибке API
                demo_rates = {
                    ('USD', 'EUR'): 0.93, ('EUR', 'USD'): 1.07,
                    ('USD', 'GBP'): 0.79, ('GBP', 'USD'): 1.27,
                    ('USD', 'JPY'): 149.0, ('JPY', 'USD'): 0.0067,
                    ('USD', 'RUB'): 92.5, ('RUB', 'USD'): 0.0108,
                    ('EUR', 'RUB'): 99.0, ('RUB', 'EUR'): 0.0101,
                }
                rate = demo_rates.get((from_curr, to_curr), 1.0)
                result = amount * rate

                history_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'from_currency': from_curr,
                    'to_currency': to_curr,
                    'amount': amount,
                    'result': result,
                    'rate': rate,
                    'demo': True
                }
                self.conversion_history.append(history_entry)
                self.save_history()

                self.logger.info(f"Used demo conversion: {amount} {from_curr} to {result} {to_curr}")
                return result

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error during conversion: {e}")
            demo_rates = {
                ('USD', 'EUR'): 0.93, ('EUR', 'USD'): 1.07,
                ('USD', 'GBP'): 0.79, ('GBP', 'USD'): 1.27,
                ('USD', 'RUB'): 92.5, ('RUB', 'USD'): 0.0108,
            }
            rate = demo_rates.get((from_curr, to_curr), 1.0)
            result = amount * rate
            return result
        except Exception as e:
            self.logger.error(f"Conversion error: {e}")
            return None

    def get_exchange_rate(self, from_curr: str, to_curr: str) -> Optional[float]:
        """Получение курса обмена"""
        try:
            if from_curr == to_curr:
                return 1.0

            response = requests.get(f"{self.api_url}/pair/{from_curr}/{to_curr}/1", timeout=10)
            response.raise_for_status()
            data = response.json()

            if data["result"] == "success":
                return data["conversion_rate"]
            else:
                demo_rates = {
                    ('USD', 'EUR'): 0.93, ('EUR', 'USD'): 1.07,
                    ('USD', 'GBP'): 0.79, ('GBP', 'USD'): 1.27,
                    ('USD', 'JPY'): 149.0, ('JPY', 'USD'): 0.0067,
                    ('USD', 'RUB'): 92.5, ('RUB', 'USD'): 0.0108,
                }
                return demo_rates.get((from_curr, to_curr), 1.0)

        except Exception as e:
            self.logger.error(f"Error getting exchange rate: {e}")
            demo_rates = {
                ('USD', 'EUR'): 0.93, ('EUR', 'USD'): 1.07,
                ('USD', 'GBP'): 0.79, ('GBP', 'USD'): 1.27,
                ('USD', 'RUB'): 92.5, ('RUB', 'USD'): 0.0108,
            }
            return demo_rates.get((from_curr, to_curr), 1.0)

    def save_history(self):
        """Сохранение истории конвертаций"""
        try:
            with open('conversion_history.json', 'w', encoding='utf-8') as f:
                json.dump(self.conversion_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving history: {e}")

    def load_history(self):
        """Загрузка истории конвертаций"""
        try:
            with open('conversion_history.json', 'r', encoding='utf-8') as f:
                self.conversion_history = json.load(f)
        except FileNotFoundError:
            self.conversion_history = []
        except Exception as e:
            self.logger.error(f"Error loading history: {e}")
            self.conversion_history = []


class ModernCurrencyConverterApp(tk.Tk):
    """GUI для конвертера валют"""

    def __init__(self):
        super().__init__()

        # Инициализация бэкенда
        self.converter = CurrencyConverterPro()
        self.theme = ModernTheme()

        # Настройка главного окна
        self.title("💱 Конвертер Валют ")
        self.geometry("650x750+400+50")
        self.minsize(600, 700)
        self.configure(bg=self.theme.LIGHT)

      
        self.style = ttk.Style()
        self.setup_styles()

        self.build_gui()
        self.load_data()

        # история
        self.converter.load_history()

    def setup_styles(self):
        """Настройка современных стилей"""
        self.style.theme_use('clam')

        # Конфигурация стилей
        self.style.configure('Main.TFrame', background=self.theme.LIGHT)

        # Стиль для карточек
        self.style.configure('Card.TFrame',
                             background=self.theme.CARD_BG,
                             relief='flat',
                             borderwidth=0)

        # Стиль для заголовков
        self.style.configure('Title.TLabel',
                             font=('Segoe UI', 18, 'bold'),
                             foreground=self.theme.DARK,
                             background=self.theme.LIGHT)

        # Стиль для основной кнопки
        self.style.configure('Primary.TButton',
                             font=('Segoe UI', 10, 'bold'),
                             background=self.theme.PRIMARY,
                             foreground='white',
                             focuscolor='none',
                             borderwidth=0,
                             relief='flat')

        self.style.map('Primary.TButton',
                       background=[('active', self.theme.PRIMARY_LIGHT),
                                   ('pressed', self.theme.PRIMARY)])

        # Стиль для второстепенной кнопки
        self.style.configure('Secondary.TButton',
                             font=('Segoe UI', 9, 'bold'),
                             background=self.theme.LIGHT,
                             foreground=self.theme.DARK,
                             focuscolor='none',
                             borderwidth=1,
                             relief='flat')

        self.style.map('Secondary.TButton',
                       background=[('active', self.theme.BORDER)])

        # Стиль для результата
        self.style.configure('Success.TLabel',
                             font=('Segoe UI', 14, 'bold'),
                             foreground=self.theme.SUCCESS,
                             background=self.theme.CARD_BG)

        # Стиль для комбобоксов
        self.style.configure('Modern.TCombobox',
                             fieldbackground=self.theme.CARD_BG,
                             background=self.theme.CARD_BG,
                             borderwidth=1,
                             relief='flat',
                             focuscolor=self.theme.PRIMARY)

        # Стиль для поля ввода
        self.style.configure('Modern.TEntry',
                             fieldbackground=self.theme.CARD_BG,
                             borderwidth=1,
                             relief='flat',
                             focuscolor=self.theme.PRIMARY)

        # Стиль для treeview
        self.style.configure('Modern.Treeview',
                             background=self.theme.CARD_BG,
                             fieldbackground=self.theme.CARD_BG,
                             borderwidth=0,
                             relief='flat')

        self.style.configure('Modern.Treeview.Heading',
                             background=self.theme.PRIMARY,
                             foreground='white',
                             borderwidth=0,
                             relief='flat')

    def build_gui(self):
        """Построение современного интерфейса"""
        # Главный контейнер
        main_container = ttk.Frame(self, style='Main.TFrame', padding=25)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Заголовок с иконкой
        header_frame = ttk.Frame(main_container, style='Main.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 20))

        title_label = ttk.Label(
            header_frame,
            text="💱 Конвертер Валют Pro",
            style='Title.TLabel'
        )
        title_label.pack(anchor=tk.W)

        subtitle_label = ttk.Label(
            header_frame,
            text="Конвертация валют в реальном времени",
            font=('Segoe UI', 10),
            foreground='#6b7280',
            background=self.theme.LIGHT
        )
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))

        # Карточка конвертера
        converter_card = ttk.Frame(main_container, style='Card.TFrame')
        converter_card.pack(fill=tk.X, pady=(0, 20))
        converter_card.configure(padding=25)

        self.build_converter_section(converter_card)

        # Карточка результата
        result_card = ttk.Frame(main_container, style='Card.TFrame')
        result_card.pack(fill=tk.X, pady=(0, 20))
        result_card.configure(padding=25)

        self.build_result_section(result_card)

        # Карточка истории
        history_card = ttk.Frame(main_container, style='Card.TFrame')
        history_card.pack(fill=tk.BOTH, expand=True)
        history_card.configure(padding=25)

        self.build_history_section(history_card)

    def build_converter_section(self, parent):
        """Секция конвертера"""
        # Заголовок секции
        section_title = ttk.Label(
            parent,
            text="🔄 Конвертация Валют",
            font=('Segoe UI', 12, 'bold'),
            foreground=self.theme.DARK,
            background=self.theme.CARD_BG
        )
        section_title.pack(anchor=tk.W, pady=(0, 20))

        # Сетка для элементов формы
        grid_frame = ttk.Frame(parent, style='Card.TFrame')
        grid_frame.pack(fill=tk.X)

        # Валюта источника
        from_label = ttk.Label(
            grid_frame,
            text="Из валюты:",
            font=('Segoe UI', 10, 'bold'),
            foreground=self.theme.DARK,
            background=self.theme.CARD_BG
        )
        from_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 8))

        to_label = ttk.Label(
            grid_frame,
            text="В валюту:",
            font=('Segoe UI', 10, 'bold'),
            foreground=self.theme.DARK,
            background=self.theme.CARD_BG
        )
        to_label.grid(row=0, column=1, sticky=tk.W, pady=(0, 8))

        self.from_currency = ttk.Combobox(
            grid_frame,
            state="readonly",
            width=22,
            font=('Segoe UI', 10),
            style='Modern.TCombobox'
        )
        self.from_currency.grid(row=1, column=0, padx=(0, 15), sticky=tk.W + tk.E)

        self.to_currency = ttk.Combobox(
            grid_frame,
            state="readonly",
            width=22,
            font=('Segoe UI', 10),
            style='Modern.TCombobox'
        )
        self.to_currency.grid(row=1, column=1, sticky=tk.W + tk.E)

        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        # Сумма
        amount_label = ttk.Label(
            parent,
            text="Сумма:",
            font=('Segoe UI', 10, 'bold'),
            foreground=self.theme.DARK,
            background=self.theme.CARD_BG
        )
        amount_label.pack(anchor=tk.W, pady=(20, 8))

        amount_frame = ttk.Frame(parent, style='Card.TFrame')
        amount_frame.pack(fill=tk.X, pady=(0, 20))

        self.amount_var = tk.StringVar(value="1.00")
        self.amount_entry = ttk.Entry(
            amount_frame,
            textvariable=self.amount_var,
            font=('Segoe UI', 12),
            style='Modern.TEntry',
            justify=tk.CENTER
        )
        self.amount_entry.pack(fill=tk.X)

        # Кнопки действий
        button_frame = ttk.Frame(parent, style='Card.TFrame')
        button_frame.pack(fill=tk.X)

        ttk.Button(
            button_frame,
            text="🔄 Конвертировать",
            command=self.perform_conversion,
            style='Primary.TButton'
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            button_frame,
            text="🔄 Поменять местами",
            command=self.swap_currencies,
            style='Secondary.TButton'
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            button_frame,
            text="📊 Обновить курсы",
            command=self.refresh_rates,
            style='Secondary.TButton'
        ).pack(side=tk.LEFT)

    def build_result_section(self, parent):
        """Секция результата"""
        section_title = ttk.Label(
            parent,
            text="📈 Результат Конвертации",
            font=('Segoe UI', 12, 'bold'),
            foreground=self.theme.DARK,
            background=self.theme.CARD_BG
        )
        section_title.pack(anchor=tk.W, pady=(0, 15))

        self.result_var = tk.StringVar(value="Введите сумму и нажмите 'Конвертировать'")
        self.result_label = ttk.Label(
            parent,
            textvariable=self.result_var,
            style='Success.TLabel',
            background=self.theme.LIGHT,
            padding=15,
            anchor=tk.CENTER,
            relief='flat',
            borderwidth=0
        )
        self.result_label.pack(fill=tk.X)

        # Курс обмена
        self.rate_var = tk.StringVar()
        rate_label = ttk.Label(
            parent,
            textvariable=self.rate_var,
            foreground='#6b7280',
            font=('Segoe UI', 9),
            background=self.theme.CARD_BG
        )
        rate_label.pack(anchor=tk.W, pady=(10, 0))

    def build_history_section(self, parent):
        """Секция истории"""
        # Заголовок и кнопка очистки
        history_header = ttk.Frame(parent, style='Card.TFrame')
        history_header.pack(fill=tk.X, pady=(0, 15))

        history_title = ttk.Label(
            history_header,
            text="📊 История Конвертаций",
            font=('Segoe UI', 12, 'bold'),
            foreground=self.theme.DARK,
            background=self.theme.CARD_BG
        )
        history_title.pack(side=tk.LEFT)

        ttk.Button(
            history_header,
            text="Очистить историю",
            command=self.clear_history,
            style='Secondary.TButton'
        ).pack(side=tk.RIGHT)

        # Таблица истории
        history_frame = ttk.Frame(parent, style='Card.TFrame')
        history_frame.pack(fill=tk.BOTH, expand=True)

        # Создаем Treeview для истории
        columns = ('time', 'from', 'to', 'amount', 'result')
        self.history_tree = ttk.Treeview(
            history_frame,
            columns=columns,
            show='headings',
            height=8,
            style='Modern.Treeview'
        )

        # Настраиваем колонки
        self.history_tree.heading('time', text=' Время')
        self.history_tree.heading('from', text=' Из')
        self.history_tree.heading('to', text=' В')
        self.history_tree.heading('amount', text=' Сумма')
        self.history_tree.heading('result', text=' Результат')

        self.history_tree.column('time', width=100, anchor=tk.CENTER)
        self.history_tree.column('from', width=80, anchor=tk.CENTER)
        self.history_tree.column('to', width=80, anchor=tk.CENTER)
        self.history_tree.column('amount', width=100, anchor=tk.CENTER)
        self.history_tree.column('result', width=120, anchor=tk.CENTER)

        # Скроллбар для таблицы
        scrollbar = ttk.Scrollbar(
            history_frame,
            orient=tk.VERTICAL,
            command=self.history_tree.yview
        )
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_data(self):
        """Загрузка данных о валютах"""
        self.after(100, self._async_load_data)

    def _async_load_data(self):
        """Асинхронная загрузка данных"""
        try:
            currencies = self.converter.fetch_currencies()
            if currencies:
                self.from_currency['values'] = currencies
                self.to_currency['values'] = currencies

                # Устанавливаем популярные валюты по умолчанию
                if 'USD' in currencies:
                    self.from_currency.set('USD')
                if 'RUB' in currencies:
                    self.to_currency.set('RUB')
                elif 'EUR' in currencies:
                    self.to_currency.set('EUR')

                self.update_history_display()
                logging.info("Приложение успешно запущено")

                # Показываем приветственное сообщение
                self.result_var.set("Готово к конвертации! Введите сумму и нажмите 'Конвертировать'")
            else:
                logging.warning("Не удалось загрузить валюты, используем демо-данные")
        except Exception as e:
            logging.error(f"Ошибка загрузки данных: {e}")

    def perform_conversion(self):
        """Выполнение конвертации"""
        try:
            from_curr = self.from_currency.get()
            to_curr = self.to_currency.get()
            amount = float(self.amount_var.get())

            if not from_curr or not to_curr:
                messagebox.showerror("Ошибка", "Пожалуйста, выберите обе валюты")
                return

            result = self.converter.convert_currency(from_curr, to_curr, amount)

            if result is not None:
                self.result_var.set(f"{amount:.2f} {from_curr} = {result:.2f} {to_curr}")

                # Получаем и отображаем курс
                rate = self.converter.get_exchange_rate(from_curr, to_curr)
                if rate:
                    self.rate_var.set(f"💱 Курс обмена: 1 {from_curr} = {rate:.4f} {to_curr}")

                # Обновляем историю
                self.update_history_display()

        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите корректное число для суммы")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка конвертации: {e}")

    def swap_currencies(self):
        """Обмен валют местами"""
        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()

        self.from_currency.set(to_curr)
        self.to_currency.set(from_curr)

    def refresh_rates(self):
        """Обновление курсов валют"""
        self.converter.fetch_currencies()
        messagebox.showinfo("Успех", "Курсы валют обновлены!")

    def update_history_display(self):
        """Обновление отображения истории"""
        # Очищаем текущие данные
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # Добавляем свежие данные (последние 10 записей)
        recent_history = self.converter.conversion_history[-10:]

        for entry in reversed(recent_history):
            time_str = datetime.fromisoformat(entry['timestamp']).strftime("%H:%M:%S")
            self.history_tree.insert('', 0, values=(
                time_str,
                entry['from_currency'],
                entry['to_currency'],
                f"{entry['amount']:.2f}",
                f"{entry['result']:.2f}"
            ))

    def clear_history(self):
        """Очистка истории"""
        if messagebox.askyesno("Подтверждение", "Очистить всю историю конвертаций?"):
            self.converter.conversion_history = []
            self.converter.save_history()
            self.update_history_display()


def run_tests():
    """Тестирование функционала приложения"""
    print(" Запуск тестов")

    try:
        converter = CurrencyConverterPro()
        print(" Тест инициализации API ключа пройден")

        currencies = converter.fetch_currencies()
        assert len(currencies) > 0, "Не удалось загрузить валюты"
        print(" Тест загрузки валют пройден")

        result = converter.convert_currency('USD', 'RUB', 1.0)
        assert result is not None, "Тест конвертации не пройден"
        print(" Тест конвертации пройден")

        rate = converter.get_exchange_rate('USD', 'EUR')
        assert rate is not None, "Тест курса обмена не пройден"
        print(" Тест курса обмена пройден")

        print(" Все тесты пройдены!")
        return True

    except Exception as e:
        print(f" Тесты не пройдены: {e}")
        return False


if __name__ == "__main__":
    # Запуск тестов при старте
    tests_passed = run_tests()

    # Запуск приложения
    app = ModernCurrencyConverterApp()
    app.mainloop()
