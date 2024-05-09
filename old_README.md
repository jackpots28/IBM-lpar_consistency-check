
# IBM-lpar_consistency-check

<p>
Gathers lpar information for individal managed systems and compares between 
"sister" systems to ensure consistency across pairs
</p>

## Examples

<p>
Given lpar_a on managed_system_a and lpar_b on managed_system_b
</p>

---

- If these managed_systems are meant to be "pairs" / close to identical:
    - checks the resource allocations in the active lpar profile of each system
    - returns only the managed_systems names and no other output if pairs match
    - if there are inconsistencies, will give the lpar id and resources that differ


## Input

<p>
Requires input of newline delimited file containing {managed_system} {managed_system_description}
</p>

---

The following code snippet can be used to generate the input file:

```
for i in $(lssyscfg -r sys -F name); do lssyscfg -m $i -r lpar -F name | xargs -n1 -I{} echo {} `lssyscfg -m $i -r sys -F description`; done
```

This snippet will require a semi-priviledged user on an HMC/vHMC - a user such as root/hscroot who can run (awk, xargs, and other functional rbash commands)

---

- {managed_system} is the name provided from the HMC / is the relative name used in commands such as lssyscfg -m ...
and  {managed_system_description} is the description provided on the systems information page
    - These values should be stored in {managed_systems.log}

- This description value will need to be consistent across both systems in the "pair" to the checked. The logic in the code utilizes the description to know which systems are "pairs"

---

<p>
All testing was done between IBM POWER 8-10 Systems and vHMC's
</p>
