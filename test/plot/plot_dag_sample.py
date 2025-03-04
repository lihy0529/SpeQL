import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import json
import re
import os
import numpy as np


# line: Q3, Q5, Q7, Q8, Q9, Q12, Q13, Q15, Q16, Q20, Q21, Q23, Q23(b), Q26, Q27, Q32, Q37, Q40, Q41, Q43, Q47, Q48, Q49, Q52, Q55, Q57, Q63, Q72, Q77, Q79, Q82, Q84, Q91, Q92, Q93, Q94, Q95, Q98 
# tree: Q1, Q2, Q4, Q6, Q11, Q17, Q18, Q19, Q22, Q24, Q24(b), Q25, Q29, Q30, Q31, Q34, Q35, Q36, Q38, Q39, Q39(b), Q42, Q45, Q46, Q50, Q53, Q54, Q59, Q62, Q64, Q66, Q67, Q68, Q70, Q71, Q73, Q74, Q75, Q81, Q85, Q86, Q89, Q96, Q99
# network: Q10, Q14, Q14(b), Q28, Q33, Q44, Q51, Q56, Q58, Q60, Q61, Q65, Q69, Q76, Q78, Q80, Q83, Q87, Q88, Q90, Q97

CREATE_TABLE_REGEX = re.compile(
    r'CREATE\s+TEMPORARY\s+TABLE\s+"([^"]+)"', re.IGNORECASE
)
REFERENCED_TABLE_REGEX = re.compile(r'(FROM|JOIN)\s+"([^"]+)"', re.IGNORECASE)

statistics = {"create_node": [], "edge_count": [], "create_size": [], "query_node": []}


def extract_number(label):
    match = re.search(r"(\d+)", label)
    return int(match.group(1)) if match else 0


def analyze_dependencies(file_path):
    elements = {}
    table_creation_map = {}
    table_query_map = {}

    dependencies = []
    if len(statistics["create_node"]) != 0:
        if statistics["create_node"][-1] == 0:
            print(file_path)
        elif statistics["query_node"][-1] == 0:
            print(file_path)

    statistics["create_node"].append(0)
    statistics["edge_count"].append(0)
    statistics["query_node"].append(0)
    statistics["create_size"].append(0)

    with open(file_path, "r", encoding="utf-8") as file:
        json_data = json.load(file)
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
                        }

                        for table in created_tables:
                            table_creation_map[table] = f"{unified_id_counter}"

                        statistics["create_node"][-1] += 1
                        statistics["edge_count"][-1] += len(referenced_tables)
                        statistics["create_size"][-1] += create_item["create_metrics"][
                            "create_size"
                        ]
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
                        }

                        if script not in table_query_map:
                            table_query_map[script] = f"{unified_id_counter}"
                        statistics["query_node"][-1] += 1
                        statistics["edge_count"][-1] += len(referenced_tables)
                        unified_id_counter += 1

    for elem_id, element in elements.items():
        if (
            element["script"] in table_query_map
            and table_query_map[element["script"]] != elem_id
        ):
            dependencies.append((table_query_map[element["script"]], elem_id))

        else:
            for table in element["referenced_tables"]:
                creator_id = table_creation_map.get(table)

                if creator_id:
                    dependencies.append((creator_id, elem_id))

    return elements, dependencies


def draw_dependency_graph(elements, dependencies, ax, title):
    dag = nx.DiGraph()

    for elem_id, elem_data in elements.items():
        dag.add_node(elem_id)

    for source, target in dependencies:
        dag.add_edge(source, target)

    node_colors = []
    for node in dag.nodes:
        if elements[node]["type"] == "CreateScript":
            node_colors.append("#ff6f61")
        elif elements[node]["type"] == "QueryScript":
            node_colors.append("#6baed6")

    pos_hierarchy = graphviz_layout(dag, prog="dot")

    num_nodes = len(dag.nodes)

    nx.draw(
        dag,
        pos_hierarchy,
        with_labels=True,
        labels={node: elements[node]["id"] for node in dag.nodes},
        node_size=250 if title == "Query 1" else 280 if title == "Query 14 (b)" else 180,
        node_color=node_colors,
        font_size=12 if title == "Query 1" else 12 if title == "Query 14 (b)" else 10,
        font_family="sans-serif",
        alpha=0.95,
        edge_color="gray",
        arrowsize=10,
        ax=ax,
        width=1,
    )
    ax.text(0.5, -0.1, "(a) Q1" if title == "Query 1" else "(b) Q14 (b)" if title == "Query 14 (b)" else "(c) Q41" if title == "Query 41" else "", 
            horizontalalignment='center',
            transform=ax.transAxes,
            fontsize=20,
            fontweight='bold'
            )


def main():
    files = [
        os.path.join(f"../dataset/create_and_query_line_by_line/100G", f)
        for f in os.listdir(f"../dataset/create_and_query_line_by_line/100G")
        if f.endswith(".json")
    ]
    files.sort(
        key=lambda file_name: int(re.search(r"tpcdsq(\d+)(_b)?", file_name).group(1))
    )

    fig, axes = plt.subplots(1, 3, figsize=(9, 3))
    axes = axes.flatten()
    i = 0
    for file_path in files:
        elements, dependencies = analyze_dependencies(file_path)
        match = re.search(r"tpcdsq(\d+)(_b)?", file_path)
        title = f"Query {match.group(1)}" + (" (b)" if match.group(2) else "")
        if title == "Query 1" or title == "Query 14 (b)" or title == "Query 41":
            draw_dependency_graph(elements, dependencies, axes[i], title)
            i += 1

    print(
        "create_node",
        "median",
        np.median(statistics["create_node"]),
        "mean",
        np.mean(statistics["create_node"]),
        "max",
        np.max(statistics["create_node"]),
        "min",
        np.min(statistics["create_node"]),
    )
    print(
        "edge_count",
        "median",
        np.median(statistics["edge_count"]),
        "mean",
        np.mean(statistics["edge_count"]),
        "max",
        np.max(statistics["edge_count"]),
        "min",
        np.min(statistics["edge_count"]),
    )
    print(
        "create_size",
        "median",
        np.median(statistics["create_size"]),
        "mean",
        np.mean(statistics["create_size"]),
        "max",
        np.max(statistics["create_size"]),
        "min",
        np.min(statistics["create_size"]),
    )
    print(
        "query_node",
        "median",
        np.median(statistics["query_node"]),
        "mean",
        np.mean(statistics["query_node"]),
        "max",
        np.max(statistics["query_node"]),
        "min",
        np.min(statistics["query_node"]),
    )

    for i in range(len(files), len(axes)):
        fig.delaxes(axes[i])

    plt.tight_layout(pad=0, h_pad=0.1, w_pad=0.1)
    plt.savefig(f"./fig/dag_sample.pdf", format="pdf", bbox_inches="tight")

    plt.show()


if __name__ == "__main__":
    main()
