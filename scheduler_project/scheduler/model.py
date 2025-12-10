import logging
from gurobipy import Model, GRB, quicksum

logger = logging.getLogger(__name__)

def solve_multi_machine(tasks,
                        time_limit=30,
                        objective="weighted_completion",
                        allow_reassign=False,
                        penalty_lateness=0.0,
                        maintenances=None,
                        staff_capacity=None,
                        time_granularity=5):

    n = len(tasks)
    if n == 0:
        return [], None, None

    J = range(n)
    # collect machines set
    machines = sorted(list({t.get('machine') for t in tasks if t.get('machine') is not None}))
    # allow additional machines if tasks include eligible_machines
    for t in tasks:
        em = t.get('eligible_machines')
        if em and isinstance(em, (list,tuple)):
            for mm in em:
                if mm not in machines:
                    machines.append(mm)
    machines = sorted(machines)
    Mset = range(len(machines))
    machine_idx = {machines[i]: i for i in Mset}

    # basic params
    p, r, w, staff = {}, {}, {}, {}
    s_setup = {i: {k: 0.0 for k in J} for i in J}
    id_to_index = {tasks[i]['id']: i for i in J}

    for i in J:
        t = tasks[i]
        p[i] = float(t.get('duration', 1.0))
        r[i] = float(t.get('release', 0.0))
        w[i] = float(t.get('priority', 1.0))
        staff[i] = t.get('staff_group', None)
        # setup after mapping: task i has setup after some other tasks
        for other_id, st in (t.get('setup_after') or {}).items():
            if other_id in id_to_index:
                k = id_to_index[other_id]
                try:
                    s_setup[i][k] = float(st)
                except Exception:
                    s_setup[i][k] = 0.0

    horizon = sum(p.values()) + max(0, max(r.values()) if r else 0) + 100

    bigM = horizon + max(max(s_setup[i].values()) for i in J)

    model = Model("Scheduler_Advanced")
    model.Params.TimeLimit = time_limit
    model.Params.OutputFlag = 0

    # Start times
    S = model.addVars(J, lb=0.0, vtype=GRB.CONTINUOUS, name='Start')
    if allow_reassign:
        y = model.addVars(J, len(machines), vtype=GRB.BINARY, name='Assign')
        for i in J:
            model.addConstr(quicksum(y[i,m] for m in Mset) == 1)
    else:
        y = None

    x = model.addVars(J, J, vtype=GRB.BINARY, name='Order')

    
    Cmax = model.addVar(vtype=GRB.CONTINUOUS, name='Cmax')

    L = model.addVars(J, lb=0.0, vtype=GRB.CONTINUOUS, name='Lateness')

    for i in J:
        for k in J:
            if i == k: 
                continue

            if allow_reassign:

                for m in Mset:
                    model.addConstr(S[i] + p[i] + s_setup[i][k] <= S[k] + bigM*(1 - x[i,k]) + bigM*(1 - (y[i,m] + y[k,m])/2))
                    model.addConstr(S[k] + p[k] + s_setup[k][i] <= S[i] + bigM*(x[i,k]) + bigM*(1 - (y[i,m] + y[k,m])/2))
            else:
                mi = tasks[i].get('machine')
                mk = tasks[k].get('machine')
                if mi is not None and mk is not None and mi == mk:
                    model.addConstr(S[i] + p[i] + s_setup[i][k] <= S[k] + bigM*(1 - x[i,k]))
                    model.addConstr(S[k] + p[k] + s_setup[k][i] <= S[i] + bigM*(x[i,k]))

            if s_setup[i][k] > 0:
                model.addConstr(S[i] >= S[k] + p[k] + s_setup[i][k])


    for i in J:
        model.addConstr(S[i] >= r[i])
        d_val = tasks[i].get('deadline', None)
        if d_val not in [None, '']:
            try:
                dval = float(d_val)
                model.addConstr(S[i] + p[i] - dval <= L[i])
            except Exception:
                pass
        else:
           
            pass

    if maintenances:
        for block in maintenances:
            mm = block.get('machine')
            a = float(block.get('start', 0))
            b = float(block.get('end', 0))
            # for tasks on same machine, either finish before a or start after b
            for i in J:
                task_m = tasks[i].get('machine')
                if allow_reassign:
                    if mm in machine_idx:
                        m_idx = machine_idx[mm]
                        model.addConstr(S[i] + p[i] <= a + bigM*(1 - y[i,m_idx]) )
                        model.addConstr(S[i] >= b - bigM*(1 - y[i,m_idx]) )
                else:
                    if task_m == mm:
                        # must be before a or after b; encode as: S[i] + p[i] <= a OR S[i] >= b
                        # emulate with x-like binary z_maint[i,block] but easier: create a binary z and two constraints
                        z = model.addVar(vtype=GRB.BINARY, name=f"z_maint_{i}_{a}_{b}")
                        model.addConstr(S[i] + p[i] <= a + bigM * z)
                        model.addConstr(S[i] >= b - bigM * (1 - z))

    staff_time_vars = None
    if staff_capacity:

        gran = max(1, int(time_granularity))
        T = list(range(0, int(horizon) + gran, gran))

        staff_time_vars = model.addVars(J, len(T), vtype=GRB.BINARY, name='run_slot')

        eps = 1e-6
        for i in J:
            for tidx, tstart in enumerate(T):
                model.addConstr(S[i] <= tstart + bigM*(1 - staff_time_vars[i,tidx]) )
                model.addConstr(S[i] + p[i] >= tstart + eps - bigM*(1 - staff_time_vars[i,tidx]) )

        for grp, cap in staff_capacity.items():

            for tidx, tstart in enumerate(T):
                model.addConstr(quicksum(staff_time_vars[i,tidx] for i in J if staff[i] == grp) <= int(cap))


    for i in J:
        model.addConstr(Cmax >= S[i] + p[i])


    #  objectives
    if objective == "makespan":
        base_obj = Cmax
    elif objective == "weighted_completion":
        base_obj = quicksum(w[i] * (S[i] + p[i]) for i in J)
    elif objective == "multi_criteria":  # fallback to weighted sum with defaults
        alpha = 1.0
        beta = 0.5
        base_obj = alpha * Cmax + beta * quicksum(w[i] * (S[i] + p[i]) for i in J)
    elif objective.startswith("lex_makespan"):

        base_obj = Cmax
    elif objective.startswith("weighted_sum"):

        parts = objective.split(':')
        if len(parts) == 3:
            alpha = float(parts[1])
            beta = float(parts[2])
        else:
            alpha = 1.0
            beta = 0.5
        base_obj = alpha * Cmax + beta * quicksum(w[i] * (S[i] + p[i]) for i in J)
    else:
        base_obj = quicksum(w[i] * (S[i] + p[i]) for i in J)


    if penalty_lateness and penalty_lateness > 0:
        obj = base_obj + penalty_lateness * quicksum(w[i] * L[i] for i in J)
    else:
        obj = base_obj

    model.setObjective(obj, GRB.MINIMIZE)


    model.optimize()

    # ---  solution ---
    solution = []
    obj_val = None
    if model.Status in [GRB.OPTIMAL, GRB.TIME_LIMIT]:
        for i in J:
            s_val = float(S[i].X) if S[i].X is not None else None
            assigned_machine = tasks[i].get('machine')
            if allow_reassign and y:
                for m in Mset:
                    if y[i,m].X > 0.5:
                        assigned_machine = machines[m]
                        break
            solution.append({
                "id": tasks[i]['id'],
                "machine": assigned_machine,
                "start": s_val,
                "end": (s_val + p[i]) if s_val is not None else None,
                "duration": p[i],
                "priority": w[i],
                "staff_group": staff[i],
            })
        obj_val = model.ObjVal
        logger.info("Solved. Obj=%.2f", obj_val)
    else:
        logger.error("Solver status: %s", model.Status)

    return solution, obj_val, model
