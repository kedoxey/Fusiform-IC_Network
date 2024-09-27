
def define_int_conns(num_cells):
    int_conn_ids = {}
    int_ids = [i for i in range(num_cells)]
    weight_pattern = [1, 2, 3, 3, 3, 2, 1]
    int_weight_patterns = {}
    for int_id in int_ids:
        l_lb, l_ub = (int_id-7, int_id-1) if int_id>0 else (0.5, 0.5)
        if l_lb < 0: l_lb = 0
        r_lb, r_ub = int_id+1, int_id+7

        left_ids = int_ids[l_lb:l_ub+1] if l_lb != 0.5 else []
        right_ids = int_ids[r_lb:r_ub+1]

        int_conn_ids[int_id] = {'left': left_ids,
                                'right': right_ids}

        left_pattern = [weight_pattern[-i-1] for i, _ in enumerate(left_ids)] if left_ids else []
        right_pattern = [weight_pattern[i] for i, _ in enumerate(right_ids)]

        int_weight_patterns[int_id] = {'left': left_pattern,
                                    'right': right_pattern}

    i2f_connList = {}

    for int_conn_id, lr_ids in int_conn_ids.items():
        temp = 5
        for side, side_ids in lr_ids.items():
            for side_i, side_id in enumerate(side_ids):
                side_weight = int_weight_patterns[int_conn_id][side][side_i]
                if side_weight in i2f_connList.keys():
                    i2f_connList[side_weight].append([int_conn_id, side_id])
                else:
                    i2f_connList[side_weight] = [[int_conn_id, side_id]]

    return i2f_connList


