def precision_recall(retrieved, relevant):
    retrieved_set = set([r["metadata"]["source"] for r in retrieved])
    relevant_set = set(relevant)

    true_pos = len(retrieved_set & relevant_set)
    precision = true_pos / len(retrieved_set) if retrieved_set else 0
    recall = true_pos / len(relevant_set) if relevant_set else 0

    return {"precision": precision, "recall": recall}
