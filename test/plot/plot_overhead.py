import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import json
import re
import os
import numpy as np

CREATE_TABLE_REGEX = re.compile(
    r'CREATE\s+TEMPORARY\s+TABLE\s+"([^"]+)"', re.IGNORECASE
)
REFERENCED_TABLE_REGEX = re.compile(r'(FROM|JOIN)\s+"([^"]+)"', re.IGNORECASE)

size = 1000

def analyze_dependencies(file_path):
    elements = {}
    table_creation_map = {}
    with open(file_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
        unified_id_counter = 1
        for label, obj in enumerate(json_data):
            if obj.get("create") and isinstance(obj["create"], list):
                for create_item in obj["create"]:
                    if create_item["create_metrics"]["execution_time"] != -1:
                        script = create_item["create"]
                        created_tables = CREATE_TABLE_REGEX.findall(script)
                        referenced_tables = REFERENCED_TABLE_REGEX.findall(script)
                        referenced_tables = [tbl for _, tbl in referenced_tables]
                        
                        elements[f"{unified_id_counter}"] = {
                            "id": f"{len(json_data) - label - 1}",
                            "type": "CreateScript",
                            "created_tables": created_tables,
                            "referenced_tables": referenced_tables,
                            "script": script,
                            "create_metrics": create_item["create_metrics"],
                            "create_metrics_warm_up": create_item["create_metrics_warm_up"],
                        }
                        
                        for table in created_tables:
                            table_creation_map[table] = f"{unified_id_counter}"

                        unified_id_counter += 1

            if obj.get("query") and isinstance(obj["query"], list):
                for query_item in obj["query"]:
                    if query_item["query_metrics"]["execution_time"] != -1:
                        script = query_item["query"]
                        referenced_tables = REFERENCED_TABLE_REGEX.findall(script)
                        referenced_tables = [tbl for _, tbl in referenced_tables]

                        elements[f"{unified_id_counter}"] = {
                            "id": f"{len(json_data) - label - 1}",
                            "type": "QueryScript",
                            "referenced_tables": referenced_tables,
                            "script": script,
                            "query_metrics": query_item["query_metrics"],
                            "query_metrics_warm_up": query_item["query_metrics_warm_up"],
                        }

                        unified_id_counter += 1

    if len(elements) > 0 and list(elements.items())[-1][1]["type"] == "QueryScript":
        root = elements[f"{len(elements)}"]
        
        execution_time_list = [0] * len(json_data)
        compile_time_list = [0] * len(json_data)
        planning_time_list = [0] * len(json_data)
        filter_set = set()
        
        def dfs(node):
            
            if node["type"] == "CreateScript":
                execution_time_list[int(node["id"])] += node["create_metrics"]["execution_time"] * 1000
                compile_time_list[int(node["id"])] += node["create_metrics_warm_up"]["compile_time"] * 1000
                planning_time_list[int(node["id"])] += node["create_metrics"]["planning_time"] * 1000
                
            for referenced_table in node["referenced_tables"]:
                if referenced_table in table_creation_map:
                    if table_creation_map[referenced_table] not in filter_set:
                        filter_set.add(table_creation_map[referenced_table])
                        dfs(elements[table_creation_map[referenced_table]])
        
        dfs(root)
        if len(execution_time_list) < 21:
            execution_time_list = execution_time_list + [0] * (21 - len(execution_time_list))
            compile_time_list = compile_time_list + [0] * (21 - len(compile_time_list))
            planning_time_list = planning_time_list + [0] * (21 - len(planning_time_list))
    else:
        execution_time_list = [0] * 21
        compile_time_list = [0] * 21
        planning_time_list = [0] * 21
    return execution_time_list, compile_time_list, planning_time_list

def create_execution_time_plot(execution_time_lists, compile_time_lists, planning_time_lists, sizes):
    fig, axes = plt.subplots(3, 3, figsize=(9, 7))
    y = np.linspace(0, 100, 103)
    
    time_lists = [planning_time_lists, compile_time_lists, execution_time_lists]
    titles = ['Planning', 'Compilation', 'Execution']
    
    for row, (time_lists_row, title) in enumerate(zip(time_lists, titles)):
        for col, (time_list, size) in enumerate(zip(time_lists_row, sizes)):
            colors = plt.cm.coolwarm(np.linspace(0, 1, len(time_list)))
            
            # axes[row, col].axvline(x=1000, color='black', linestyle='--', alpha=0.5)
            
            for i in range(len(time_list)):
                if i != len(time_list) - 1:
                    axes[col, row].fill_betweenx(y, time_list[i+1], time_list[i],
                                   alpha=0.8, 
                                   color=colors[i], 
                                   label=f'#{20-i}' if row == 0 and col == 0 else "")
                else:
                    axes[col, row].fill_betweenx(y, 0, time_list[i],
                                   alpha=0.8,
                                   color=colors[i],
                                   label=f'#{20-i}' if row == 0 and col == 0 else "")
            
            axes[col, row].set_xscale('log')
            # only the last row has xlabel
            if col == 2:  # 现在是最后一列显示xlabel
                axes[col, row].set_xlabel(f'{title} (ms)', fontsize=20, fontweight='bold')
            if row == 0:  # 现在是第一行显示ylabel
                axes[col, row].set_ylabel(f'{size}GB\nCDF (%)', fontsize=20, fontweight='bold')
            axes[col, row].grid(True, axis='both', alpha=0.3, linestyle='--')
            axes[col, row].set_ylim(bottom=0, top=100)
            axes[col, row].set_yticks([20, 40, 60, 80, 100])
            if row != 0:
                axes[col, row].set_yticklabels([])
            axes[col, row].tick_params(axis='both', labelsize=16)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, 
              bbox_to_anchor=(0.5, 1.08),
              loc='center',
              fontsize=13.5,
              ncol=7) 
    
    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=0.5)
    return fig

def main():
    sizes = [10, 100, 1000]
    all_execution_time_lists = []
    all_compile_time_lists = []
    all_planning_time_lists = []
    
    for size in sizes:
        files = [
            os.path.join(f"../dataset/create_and_query_line_by_line/{size}G", f)
            for f in os.listdir(f"../dataset/create_and_query_line_by_line/{size}G")
            if f.endswith(".json")
        ]
        
        files.sort(
            key=lambda file_name: int(re.search(r"tpcdsq(\d+)(_b)?", file_name).group(1))
        )

        execution_time_list = []
        compile_time_list = []
        planning_time_list = []
        
        for file in files:
            analyze = analyze_dependencies(file)
            execution_time_list.append(analyze[0])
            compile_time_list.append(analyze[1])
            planning_time_list.append(analyze[2])
        
        for i in range(len(execution_time_list)):
            for j in reversed(range(len(execution_time_list[i]))):
                execution_time_list[i][j] += (execution_time_list[i][j+1] if j+1 < len(execution_time_list[i]) else 0)
                compile_time_list[i][j] += (compile_time_list[i][j+1] if j+1 < len(compile_time_list[i]) else 0)
                planning_time_list[i][j] += (planning_time_list[i][j+1] if j+1 < len(planning_time_list[i]) else 0)
        
        execution_time_list = list(zip(*execution_time_list))
        compile_time_list = list(zip(*compile_time_list))
        planning_time_list = list(zip(*planning_time_list))
        execution_time_list = [sorted(list(item)) for item in execution_time_list]
        compile_time_list = [sorted(list(item)) for item in compile_time_list]
        planning_time_list = [sorted(list(item)) for item in planning_time_list]
        all_execution_time_lists.append(execution_time_list)
        all_compile_time_lists.append(compile_time_list)
        all_planning_time_lists.append(planning_time_list)
        print(execution_time_list[16])
        print(len(execution_time_list[0]))
        print(len([item for item in execution_time_list[0] if item > 1000]))
    fig = create_execution_time_plot(all_execution_time_lists, all_compile_time_lists, all_planning_time_lists, sizes)
    fig.savefig(f"./fig/overhead.pdf", format="pdf", bbox_inches="tight")
    
if __name__ == "__main__":
    main()
