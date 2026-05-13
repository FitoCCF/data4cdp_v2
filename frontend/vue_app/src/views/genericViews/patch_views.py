import os
import re

directory = '.'

def patch_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    # --- TIPO 1: Vistas que usan colKeys.forEach (TasksView, STasksViews, UserPsView, UsersView) ---
    pattern_colkeys = re.compile(r'colKeys\.forEach\(\(.*?\)\s*=>\s*\{.*?\}\);', re.DOTALL)
    if pattern_colkeys.search(content):
        replacement_colkeys = """
                const numericKeys = [
                    'n1fe', 'n2cu', 'n3zn', 'n4mo', 'n5ech5', 'n6sc', 'n7ech7',
                    'pFe', 'pCu', 'pZn', 'pMo', 'pIns', 'pSol',
                    'tara', 'tweight', 'dweight', 'pweight',
                    'a1fe', 'a2cu', 'a3zn', 'a4mo', 'a5a5', 'a6sol', 'a7a7'
                ];
                colKeys.forEach((key, idx) => {
                    if (key.includes('__')) return; // Saltar columnas readonly
                    
                    let val = row[idx];
                    
                    if (typeof val === 'string') {
                        val = val.trim();
                        if (numericKeys.includes(key) && val.includes(',')) {
                            val = val.replace(',', '.');
                        }
                    }

                    let payloadKey = key;
                    if (key === 'task') payloadKey = 'task_id';
                    else if (key === 'usuario') payloadKey = 'usuario_id';
                    else if (key === 'estado') payloadKey = 'estado_id';
                    else if (key === 'user') payloadKey = 'user_id';
                    else if (key === 'group' && colKeys.includes('task')) payloadKey = 'usuario_id';
                    else if (key === 'group') payloadKey = 'group_id';
                    
                    payload[payloadKey] = (val === '' || val === null) ? null : val;
                });"""
        content = pattern_colkeys.sub(replacement_colkeys.strip(), content)

    # --- TIPO 2: Vistas que mapean manualmente (PlantsView, AreasView, SystemsView, EquipmentsView, SamplesView) ---
    # Buscamos donde declaran payload = { ... }
    # Ej: const payload = { tag: row[1], name: row[2] ... }
    # y lo reemplazamos inyectando una funcion sanitize.
    
    pattern_payload_manual = re.compile(r'const payload = \{([\s\S]*?)\};')
    
    def manual_replacer(match):
        inner = match.group(1)
        # Check if already sanitized
        if 'sanitize(' in inner:
            return match.group(0)
            
        new_inner = []
        for line in inner.split('\n'):
            if ':' in line:
                parts = line.split(':', 1)
                key = parts[0]
                val = parts[1].rstrip(',')
                if 'row[' in val:
                    new_inner.append(f"{key}: sanitize({val.strip()}),")
                else:
                    new_inner.append(line)
            else:
                new_inner.append(line)
                
        return """
          const sanitize = (val) => {
              if (typeof val === 'string') {
                  val = val.trim();
                  // Reemplazar comas por puntos si parece un número
                  if (val.includes(',') && !isNaN(val.replace(',', '.'))) {
                      val = val.replace(',', '.');
                  }
              }
              return (val === '' || val === null) ? null : val;
          };

          const payload = {""" + '\n'.join(new_inner) + "\n          };"

    # Only apply Type 2 to specific files
    if filepath in ['PlantsView.vue', 'AreasView.vue', 'SystemsView.vue', 'EquipmentsView.vue', 'SamplesView.vue']:
        content = pattern_payload_manual.sub(manual_replacer, content)

    # --- TIPO 3: MonthlyCalendarView y WeeklyTasksView ---
    # En MonthlyCalendarView:  const payload = { task_id: item.taskId, user_id: val, ...}
    # Solo agregaremos el sanitize para el valor que recogen, pero es mejor dejarlo como string .trim() para estos
    # o aplicar el manual replacer en todos
    if filepath in ['MonthlyCalendarView.vue', 'WeeklyTasksView.vue', 'GroupScheduleView.vue']:
        content = pattern_payload_manual.sub(manual_replacer, content)

    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Patched: {filepath}")
    else:
        print(f"No changes made to: {filepath}")

views = [
    'PlantsView.vue', 'AreasView.vue', 'SystemsView.vue', 'EquipmentsView.vue',
    'SamplesView.vue', 'TasksView.vue', 'STasksViews.vue', 'GroupScheduleView.vue',
    'MonthlyCalendarView.vue', 'UserPsView.vue', 'UsersView.vue', 'WeeklyTasksView.vue'
]

for view in views:
    if os.path.exists(view):
        patch_file(view)
    else:
        print(f"File not found: {view}")
