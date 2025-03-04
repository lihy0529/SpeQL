import os
import json
import re
import numpy as np
import matplotlib.pyplot as plt

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
    inference_cost = []
    
    for file in files_debug:
        with open(file, "r", encoding="utf-8") as f:
            inference_time.append([])
            inference_cost.append([])
            json_data = json.load(f)
            for item in json_data:
                inference_time[-1].append(0)
                inference_cost[-1].append(0)
                if item["debug_info"] is not None:
                    for debug_item in item["debug_info"]:
                        if debug_item["task"] != "middle":
                            inference_time[-1][-1] += debug_item["time"] * 1000
                            if debug_item["task"] != "simple":
                                inference_cost[-1][-1] += debug_item["output_tokens"]/1000000*30
                        else:
                            if inference_time[-1][-1] != 0:
                                inference_time[-1][-1] = max(inference_time[-1][-1], debug_item["time"] * 1000) 
                            else:
                                inference_time[-1][-1] = 0
                            
            if len(inference_time[-1]) != 21:
                inference_time[-1] = [0] * (21 - len(inference_time[-1])) + inference_time[-1]
                inference_cost[-1] = [0] * (21 - len(inference_cost[-1])) + inference_cost[-1]
    
    for i in range(len(inference_time)):
        for j in reversed(range(len(inference_time[i]))):
            inference_time[i][j] += (inference_time[i][j+1] if j+1 < len(inference_time[i]) else 0)
            inference_cost[i][j] += (inference_cost[i][j+1] if j+1 < len(inference_cost[i]) else 0)
    inference_time = np.array(inference_time).T.tolist()
    for i in range(len(inference_time)):
        inference_time[i] = sorted(inference_time[i])
    inference_cost = np.array(inference_cost).T.tolist()
    for i in range(len(inference_cost)):
        inference_cost[i] = sorted(inference_cost[i])
    print(inference_time)
    return inference_time, inference_cost


inference_time, inference_cost = fetch_inference_time()


def plot_inference_metrics(inference_time, inference_cost):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.5))
    
    y = np.linspace(0, 100, 103)
    colors = plt.cm.Reds(np.linspace(0, 1, len(inference_time)))

    for i in range(len(inference_time)):
        ax1.fill_betweenx(y, 0, inference_time[i],
                         alpha=1,
                         color=colors[i],
                         label=f'#{len(inference_time)-1-i}')
    
    ax1.set_xscale('log')
    ax1.set_ylabel('CDF (%)', fontsize=20, fontweight='bold')
    ax1.set_xlabel('(a) Elapsed Time (ms)', fontsize=20, fontweight='bold')
    ax1.grid(True, axis='both', alpha=0.3, linestyle='--')
    ax1.set_yticks([20, 40, 60, 80, 100])
    ax1.set_ylim(bottom=0, top=100)
    
    ax1.tick_params(axis='y', labelsize=20)
    ax1.tick_params(axis='x', labelsize=20)
    
    for i in range(len(inference_cost)):
        ax2.fill_betweenx(y, 0, inference_cost[i],
                         alpha=1,
                         color=colors[i],
                         label=f'#{len(inference_cost)-1-i}')
    
    ax2.set_xscale('log')
    ax2.grid(True, axis='both', alpha=0.3, linestyle='--')
    ax2.set_yticks([20, 40, 60, 80, 100])
    ax2.set_yticklabels([])
    ax2.set_xlabel('(b) Price ($)', fontsize=20, fontweight='bold')
    
    ax2.set_ylim(bottom=0, top=100)
    ax2.tick_params(axis='x', labelsize=20)
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, 
              bbox_to_anchor=(0.5, 1.1),
              loc='center',
              fontsize=14,
              ncol=7)
    
    plt.tight_layout()
    plt.savefig("./fig/inference.pdf", format="pdf", bbox_inches="tight")

if __name__ == "__main__":
    plot_inference_metrics(inference_time, inference_cost)