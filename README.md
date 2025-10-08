# time-management
Day plan, rules of day planning etc.

```mermaid
flowchart TD
%% === Основной поток приложения ===
A[Start winblock] --> B[Инициализация конфигурации (config.py)]
B --> C[Загрузка week-plan.yaml из GitHub через update_plan()]
C --> D[Запуск потоков: deprecated / sometimes / often / hourly]
D --> E[Вход в главный цикл main_loop() в block.py]

%% === Главный цикл ===
subgraph MAIN_LOOP[Главный цикл block.py]
    E --> F[Проверка времени и задач get_current_active_tasks() -> logic.py]
    F --> G[Получение активного окна get_active_window_title() -> system.py]
    G --> H{Активное окно разрешено в текущем интервале?}
    H -- Да --> I[Продолжить работу (ничего не сворачивать)]
    H -- Нет --> J[Вызов handle_active_window() -> minimize_window() system.py]
    J --> E
end

%% === Параллельные проверки ===
subgraph THREADS[Потоки проверки окон]
    direction TB
    T1[deprecated_windows -> check_and_minimize_deprecated_windows()]
    T2[sometimes -> check_and_minimize_timed_windows()]
    T3[often -> check_and_minimize_often_windows()]
    T4[hourly -> check_and_minimize_hourly_windows()]
end

E --> THREADS

%% === Обновление плана ===
subgraph UPDATE_PLAN[Обновление расписания]
    U1[update_plan() -> logic.py] --> U2[update_local_repo() -> system.py]
    U2 --> U3[load_week_plan() -> system.py]
end

E --> U1
U3 --> F

%% === Обработка ошибок ===
subgraph ERROR_HANDLING[Глобальная обработка ошибок]
    direction TB
    X1[thread_exception_handler()]
    X2[global_exception_handler()]
end

E -.-> X1
B -.-> X2

%% === Завершение ===
I --> Z[End / Sleep до следующей проверки]

%% === Стили ===
classDef file fill:#2c3e50,stroke:#ecf0f1,stroke-width:1px,color:#ecf0f1;
classDef process fill:#3498db,color:white;
classDef decision fill:#f39c12,color:black;
classDef loop fill:#9b59b6,color:white;

class A,B,C,D,E,F,G,I,J,Z,U1,U2,U3 file;
class H decision;
class THREADS,MAIN_LOOP,UPDATE_PLAN loop;
```