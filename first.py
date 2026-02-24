from queue import Queue
from threading import Thread, Lock
from PIL import Image, ImageOps
import os
import time
OUTPUT_DIR = 'output'
INPUT_DIR = "img"
def produceri(image_files, task_queue, num_consumers):
    print(f"Producer: начинаю добавлять {len(image_files)} изображений")
    for img_file in image_files:
        if os.path.exists(img_file):
            task_queue.put(img_file)
            print(f"Producer: добавлено {os.path.basename(img_file)}")
        else:
            print(f"Producer: файл {img_file} не найден, пропускаю")
    
    
    for _ in range(num_consumers):
        task_queue.put(None)
    print("Producer: все задачи добавлены, отправлены сигналы завершения")

def consumeri(consumer_id, task_queue, results, results_lock):
    processed_count = 0
    print(f"Consumer {consumer_id}: запущен")
    
    while True:
        task = task_queue.get()     
        
        if task is None:
            print(f"Consumer {consumer_id}: получен сигнал завершения, обработано {processed_count} задач")
            task_queue.task_done()
            break  
        print(f"Consumer {consumer_id}: начал обработку {os.path.basename(task)}")
        
        try:
            
            with Image.open(task) as img:
                
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
            
                inverted = ImageOps.invert(img)

                
                os.makedirs(OUTPUT_DIR , exist_ok=True)


                
                base_name = os.path.splitext(os.path.basename(task))[0]
                file_name = f"inverted_{base_name}_{consumer_id}.jpg"

                
                output_path = os.path.join("output", file_name) 

                
                inverted.save(output_path)

                
                with results_lock:
                    results.append(f"OK: {task} -> {output_path} (consumer {consumer_id})")
                
                print(f"Consumer {consumer_id}: готово {output_path}")
                
        except Exception as e:
            with results_lock:
                results.append(f"ERROR: {task} - {str(e)} (consumer {consumer_id})")
            print(f"Consumer {consumer_id}: ошибка при обработке {task}: {e}")
        
        finally:
            processed_count += 1  
    return processed_count


def main():
    existing_images = [
    os.path.abspath(os.path.join(INPUT_DIR, f)) 
    for f in os.listdir(INPUT_DIR) 
    if os.path.isfile(os.path.join(INPUT_DIR, f)) and f.lower().endswith('.jpg')
    ]
    if not existing_images:
        print("Нет изображений для обработки!")
        return
    
    print(f"Найдено изображений для обработки: {[os.path.basename(f) for f in existing_images]}")
    NUM_CONSUMERS = (len(existing_images) // 4) + 1
    print(f'Будет создано {NUM_CONSUMERS} consumerov')
    task_queue = Queue()
    results = []
    results_lock = Lock()
    producer = Thread(target=produceri, 
                      args=(existing_images, task_queue, NUM_CONSUMERS))
    
    consumers = []
    for i in range(NUM_CONSUMERS):
        consumer = Thread(target=consumeri, 
                         args=(i + 1, task_queue, results, results_lock))
        consumers.append(consumer)
    
  
    print("\n" + "="*50)
    print("ЗАПУСК ПОТОКОВ")
    print("="*50)
    
    start_time = time.time()

    for c in consumers:
        c.start()

    producer.start()

    producer.join()
    print("\nProducer завершил работу")
    
    for c in consumers:
        c.join()
    
    elapsed_time = time.time() - start_time
    
    print("\n" + "="*50)
    print("РЕЗУЛЬТАТЫ ОБРАБОТКИ")
    print("="*50)
    print(f"Время выполнения: {elapsed_time:.2f} секунд")
    print(f"Всего результатов: {len(results)}")
    
    for result in results:
        print(f"{result}")
    
    print("\nСозданные файлы:")
    for file in os.listdir(OUTPUT_DIR):
        if file.startswith('inverted_'):
            print(f"  {file}")

if __name__ == "__main__":
    main()