import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import json
import re
import os
import numpy as np

def fetch_latency(size):
    
    files_baseline = [
        os.path.join(f"../dataset/create_and_query_baseline/{size}G", f)
        for f in os.listdir(f"../dataset/create_and_query_baseline/{size}G")
        if f.endswith(".json")
    ]
    files_baseline.sort(
        key=lambda file_name: int(re.search(r"tpcdsq(\d+)(_b)?", file_name).group(1))
    )
    
    files_line_by_line = [
        os.path.join(f"../dataset/create_and_query_line_by_line/{size}G", f)
        for f in os.listdir(f"../dataset/create_and_query_line_by_line/{size}G")
        if f.endswith(".json")
    ]
    
    files_line_by_line.sort(
        key=lambda file_name: int(re.search(r"tpcdsq(\d+)(_b)?", file_name).group(1))
    )
    
    baseline_latency = []
    line_by_line_latency = []
    for file in files_baseline:
        with open(file, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            json_data = json_data["query"][0]
            baseline_latency.append({
                "execution_time": json_data["query_metrics"]["execution_time"],
                "compile_time": json_data["query_metrics_warm_up"]["compile_time"],
                "planning_time": json_data["query_metrics"]["planning_time"],
            })
    
    for file in files_line_by_line:
        with open(file, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            json_data = json_data[-1]["query"][0]
            if json_data["query_metrics"]["compile_time"] >= 0:
                line_by_line_latency.append({
                    "execution_time": json_data["query_metrics"]["execution_time"],
                    "compile_time": json_data["query_metrics_warm_up"]["compile_time"],
                    "planning_time": json_data["query_metrics"]["planning_time"],
                })
            else:
                line_by_line_latency.append(
                    baseline_latency[len(line_by_line_latency)].copy()
                )
                 
    line_by_line_latency = {
        "execution_time": [latency["execution_time"] for latency in line_by_line_latency],
        "compile_time": [latency["compile_time"] for latency in line_by_line_latency],
        "planning_time": [latency["planning_time"] for latency in line_by_line_latency],
    }
    baseline_latency = {
        "execution_time": [latency["execution_time"] for latency in baseline_latency],
        "compile_time": [latency["compile_time"] for latency in baseline_latency],
        "planning_time": [latency["planning_time"] for latency in baseline_latency],
    }
    
    line_by_line_latency["execution_time"].sort()
    line_by_line_latency["compile_time"].sort()
    line_by_line_latency["planning_time"].sort()
    baseline_latency["execution_time"].sort()
    baseline_latency["compile_time"].sort()
    baseline_latency["planning_time"].sort()
    
    # if size == 1000:
    #     for type in ["execution_time", "compile_time", "planning_time"]:
    #         print(line_by_line_latency[type])
    #         print(baseline_latency[type])
    #         speedup = []
    #         for i in range(len(line_by_line_latency[type])):
    #             speedup.append(1- (line_by_line_latency[type][i] / baseline_latency[type][i]))
    #             if speedup[i] <0.5:
    #                 print(files_line_by_line[i])
    #         print("type: ", type)
    #         print("speedup: ", speedup[int(len(speedup)*0.8)])
    #         print("line by line: ", line_by_line_latency[type][int(len(line_by_line_latency[type])*0.8)])
    #         print("baseline: ", baseline_latency[type][int(len(baseline_latency[type])*0.8)])
        # exit()

    return line_by_line_latency, baseline_latency
    
    exit()
    plt.tight_layout(pad=0, h_pad=0.1, w_pad=0.1)
    plt.savefig(f"./fig/latency_{size}G.pdf", format="pdf", bbox_inches="tight")

    plt.show()

def plot_metric(i, j, ax, line_by_line_data, baseline_data, title, alpha=0.6):
    line_color = '#FF9999'
    baseline_color = '#FFE5B4'
    
    # 计算百分比作为y轴
    y = np.linspace(0, 100, len(baseline_data))
    
    # 转换为毫秒
    baseline = ax.fill_betweenx(y, 0, [item * 1000 for item in baseline_data],
                             alpha=alpha, color=baseline_color, label='Baseline')
    # line = ax.fill_betweenx(y, 0, [item * 1000 for item in line_by_line_data],
    #                       alpha=alpha, color=line_color, label='Line-by-line')
    line = ax.fill_betweenx(y, 0, [item * 1000 for item in line_by_line_data],
                          alpha=alpha, color=line_color, label='Line-by-line')
    ax.set_xscale('log')
    ax.grid(True, axis='both', linestyle='--', alpha=0.3)
    
    ax.tick_params(axis='both', labelsize=16)
    if i != 0:
        ax.set_yticklabels([])
    # 显示所有边框
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1.0)  # 设置边框宽度
        spine.set_color('black')  # 设置边框颜色
    
    ax.axvline(x=500, color='black', linestyle='--', alpha=0.5)
    
    ax.set_ylim(0, 100)
    
    # 设置y轴标签
    # if i == 0:  # 第一列
    #     ax.set_ylabel('CDF (%)', fontsize='large')
    
    if j == 2:  # 最后一行
        ax.set_xlabel(title, fontsize=20, fontweight='bold')
    
    return [baseline, line], ['Baseline', 'SpeQL']

if __name__ == "__main__":
    line_by_line_latency_10G, baseline_latency_10G = fetch_latency(10)
    print(baseline_latency_10G["execution_time"])
    line_by_line_latency_100G, baseline_latency_100G = fetch_latency(100)  
    print("-"*100) 
    print(baseline_latency_100G["execution_time"])
    line_by_line_latency_1000G, baseline_latency_1000G = fetch_latency(1000)
    print("-"*100)
    print(baseline_latency_1000G["execution_time"])
    
    metrics = ['planning_time', 'compile_time', 'execution_time']
    sizes = [10, 100, 1000]
    data = {
        10: (line_by_line_latency_10G, baseline_latency_10G),
        100: (line_by_line_latency_100G, baseline_latency_100G),
        1000: (line_by_line_latency_1000G, baseline_latency_1000G)
    }
    
    fig, axes = plt.subplots(3, 3, figsize=(9, 7))
    
    plt.tight_layout(rect=[0.05, 0, 1, 0.90])
    
    titles = ['10GB\nCDF (%)', '100GB\nCDF (%)', '1000GB\nCDF (%)']#['Planning Latency (ms)', 'Compilation Latency (ms)', 'Execution Latency (ms)']
    for i, title in enumerate(titles):
        fig.text(-0.05, 0.84 - i*0.32, title, 
                rotation=90, 
                verticalalignment='center',
                fontsize=20,
                fontweight='bold')
    
    handles, labels = plot_metric(0, 0, axes[0, 0], 
                                data[10][0]['planning_time'], 
                                data[10][1]['planning_time'], 
                                '10G')
    fig.legend([handles[1], handles[0]], [labels[1], labels[0]], 
              loc='upper center', 
              bbox_to_anchor=(0.5, 1.08),
              ncol=2, 
              frameon=True, 
              fontsize=20,
              fancybox=True,
              shadow=False,
              bbox_transform=fig.transFigure,
              borderpad=0.5,
              edgecolor='gray',
              facecolor='white'
              )
    
    label = ["Planning (ms)", "Compilation (ms)", "Execution (ms)"]
    for i, metric in enumerate(metrics):
        for j, size in enumerate(sizes):
            if not (i == 0 and j == 0):
                line_by_line, baseline = data[size]
                plot_metric(i, j, axes[j, i], line_by_line[metric], baseline[metric], label[i])
    
    plt.tight_layout()
    plt.savefig(f"./fig/latency.pdf", format="pdf", bbox_inches="tight")
    plt.show()