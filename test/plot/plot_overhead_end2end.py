import os
import json
import re
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 定义要使用的分位数 (0-100之间)
PERCENTILE = 75  # 可以改成任意想要的分位数

def fetch_inference_time():
    
    files_debug = [
        os.path.join(f"../dataset/debug_line_by_line", f)
        for f in os.listdir(f"../dataset/debug_line_by_line")
        if f.endswith(".json")
    ]
    files_debug.sort(
        key=lambda file_name: int(re.search(r"tpcdsq(\d+)(_b)?", file_name).group(1))
    )
    
    inference_time = []
    
    for file in files_debug:
        with open(file, "r", encoding="utf-8") as f:
            inference_time.append([])
            json_data = json.load(f)
            for item in json_data:
                inference_time[-1].append(0)
                if item["debug_info"] is not None:
                    for debug_item in item["debug_info"]:
                        if debug_item["task"] != "middle":
                            inference_time[-1][-1] += debug_item["time"] * 1000
                        else:
                            if inference_time[-1][-1] != 0:
                                inference_time[-1][-1] = max(inference_time[-1][-1], debug_item["time"] * 1000) 
                            else:
                                inference_time[-1][-1] = 0
                            
            if len(inference_time[-1]) != 21:
                inference_time[-1] = [0] * (21 - len(inference_time[-1])) + inference_time[-1]
    

    return inference_time


inference_time = fetch_inference_time()

def fetch_query_time(size):
    files_query = [
        os.path.join(f"../dataset/create_and_query_baseline/{size}", f)
        for f in os.listdir(f"../dataset/create_and_query_baseline/{size}")
        if f.endswith(".json")
    ]
    query_execution_time = []
    query_elapsed_time = []
    query_elapsed_time_with_timeout = []
    for file in files_query:
        with open(file, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            query_execution_time.append(json_data["query"][0]["query_metrics_warm_up"]["execution_time"] * 1000)
            query_elapsed_time.append(json_data["query"][0]["query_metrics_warm_up"]["elapsed_time"] * 1000)
            query_elapsed_time_with_timeout.append(json_data["query"][0]["query_metrics_warm_up"]["elapsed_time"] * 1000)
    return query_execution_time, query_elapsed_time, query_elapsed_time_with_timeout



def fetch_database_time(size):
    files_create_and_query = [
        os.path.join(f"../dataset/create_and_query_line_by_line/{size}", f)
        for f in os.listdir(f"../dataset/create_and_query_line_by_line/{size}")
        if f.endswith(".json")
    ]
    files_create_and_query.sort(
        key=lambda file_name: int(re.search(r"tpcdsq(\d+)(_b)?", file_name).group(1))
    )
    database_execution_time = []
    database_elapsed_time = []
    database_elapsed_time_with_timeout = []
    for file in files_create_and_query:
        with open(file, "r", encoding="utf-8") as f:
            database_execution_time.append([])
            database_elapsed_time.append([])
            database_elapsed_time_with_timeout.append([])
            json_data = json.load(f)
            for item in json_data:
                database_execution_time[-1].append(0)
                database_elapsed_time[-1].append(0)
                database_elapsed_time_with_timeout[-1].append(0)
                if item["create"] is not None:
                    for create_item in item["create"]:
                        if create_item["create_metrics_warm_up"]["execution_time"] != -1:
                            database_execution_time[-1][-1] += create_item["create_metrics_warm_up"]["execution_time"] * 1000
                            database_elapsed_time[-1][-1] += create_item["create_metrics_warm_up"]["elapsed_time"] * 1000
                            database_elapsed_time_with_timeout[-1][-1] += create_item["create_metrics_warm_up"]["elapsed_time"] * 1000
                        elif create_item["create_metrics_warm_up"]["elapsed_time"] != -1:
                            database_elapsed_time_with_timeout[-1][-1] += create_item["create_metrics_warm_up"]["elapsed_time"] * 1000
                if item["query"] is not None:
                    for query_item in item["query"]: # only one
                        if query_item["query_metrics_warm_up"]["execution_time"] != -1:
                            database_execution_time[-1][-1] += query_item["query_metrics_warm_up"]["execution_time"] * 1000
                            database_elapsed_time[-1][-1] += query_item["query_metrics_warm_up"]["elapsed_time"] * 1000
                            database_elapsed_time_with_timeout[-1][-1] += query_item["query_metrics_warm_up"]["elapsed_time"] * 1000
                        elif query_item["query_metrics_warm_up"]["elapsed_time"] != -1:
                            database_elapsed_time_with_timeout[-1][-1] += query_item["query_metrics_warm_up"]["elapsed_time"] * 1000
            if len(database_execution_time[-1]) != 21:
                database_execution_time[-1] = [0] * (21 - len(database_execution_time[-1])) + database_execution_time[-1]
                database_elapsed_time[-1] = [0] * (21 - len(database_elapsed_time[-1])) + database_elapsed_time[-1]
                database_elapsed_time_with_timeout[-1] = [0] * (21 - len(database_elapsed_time_with_timeout[-1])) + database_elapsed_time_with_timeout[-1]
    return database_execution_time, database_elapsed_time, database_elapsed_time_with_timeout

sizes = ["10G", "100G", "1000G"]

# Create one figure with nine subfigures (3x3)
fig, axes = plt.subplots(3, 3, figsize=(9, 7))

percentiles = [25, 50, 75]
titles = ['P25 (ms)', 'P50 (ms)', 'P75 (ms)']

# Add row titles
for i, title in enumerate(titles):
    fig.text(-0.02, 0.84 - i*0.31, title, 
            rotation=90, 
            verticalalignment='center',
            fontsize=20,
            fontweight='bold')

for row_idx, percentile in enumerate(percentiles):
    for idx, size in enumerate(sizes):
        database_execution_time, database_elapsed_time, database_elapsed_time_with_timeout = fetch_database_time(size)
        database_execution_time_baseline, database_elapsed_time_baseline, database_elapsed_time_with_timeout_baseline = fetch_query_time(size)
        
        # 计算指定分位数
        database_execution_time_baseline_p = [np.percentile(database_execution_time_baseline, percentile)]
        database_elapsed_time_baseline_p = [np.percentile(database_elapsed_time_baseline, percentile)]
        database_elapsed_time_with_timeout_baseline_p = [np.percentile(database_elapsed_time_with_timeout_baseline, percentile)]
        
        # Get current axis
        ax = axes[row_idx, idx]
        
        # 使用不同的颜色
        colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728']
        
        # 为每个数据类别创建散点图和中位线
        categories = [
            (database_execution_time, 'DB exec w/o timeout', colors[0]),
            (database_elapsed_time, 'DB elapsed w/o timeout', colors[1]),
            (database_elapsed_time_with_timeout, 'DB elapsed w/ timeout', colors[2]),
            ([[database_elapsed_time_with_timeout[i][j] + inference_time[i][j] for j in range(21)] for i in range(len(database_elapsed_time_with_timeout))], 'Total (DB + LLM)', colors[3])
        ]
        
        # 添加基准线
        ax.axhline(y=database_execution_time_baseline_p[0], color='#1f77b4', 
                   linestyle='--', alpha=1, linewidth=1.5)
        ax.axhline(y=database_elapsed_time_with_timeout_baseline_p[0], color='#ff7f0e', 
                   linestyle='--', alpha=1, linewidth=1.5)
        
        # 绘制散点图和中位线
        for cat_idx, (data, label, color) in enumerate(categories):
            percentiles_line = [np.percentile([run_data[i] for run_data in data], percentile) for i in range(21)]
            ax.plot(range(21), percentiles_line, color=color, lw=1, linestyle='-', 
                    marker='o', markersize=5, markerfacecolor='white', 
                    markeredgecolor=color, label=label if row_idx == 0 and idx == 0 else "")
        
        if row_idx == 2:
            ax.set_xticks([0, 10, 20], ["#20", "#10", "#0"], fontsize=16)
        else:
            ax.set_xticks([0, 10, 20], [])
        ax.set_yscale('log')
        if idx == 0:
            #only the first column show the yticks
            ax.set_yticks([10, 1000, 100000])
        else:
            ax.set_yticks([10, 1000, 100000], [])
            
        ax.tick_params(axis='y', labelsize=16)
        
        if row_idx == 2:
            ax.set_xlabel(f"{size}B", fontsize=20, fontweight='bold')
        
        ax.grid(True, axis='y', linestyle='--', alpha=0.8, linewidth=1)
        ax.set_ylim(5, 100000)

# Add legend at the top
handles, labels = axes[0, 0].get_legend_handles_labels()
fig.legend(handles, labels, loc='upper center', 
          bbox_to_anchor=(0.48, 1.15),
          ncol=2, 
          frameon=True, 
          fontsize=20,
          fancybox=True,
          shadow=False,
          bbox_transform=fig.transFigure,
          borderpad=0.5,
          edgecolor='gray',
          facecolor='white')

plt.tight_layout()
plt.savefig(f"./fig/overhead_end2end_combined.pdf", format="pdf", bbox_inches="tight")
plt.close()