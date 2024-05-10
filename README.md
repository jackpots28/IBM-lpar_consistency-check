[![Licence](https://img.shields.io/github/license/Ileriayo/markdown-badges?style=for-the-badge)](./LICENSE)

![Podman](https://a11ybadges.com/badge?logo=podman)

# IBM-lpar_consistency-check

Consistency check across multiple IBM Power Frame LPAR's using Python and Podman/Docker

- Outputs CSV files to a specified directory with specific "resource differences" between two "Sister" IBM Power Frames
## Installation

Install using Podman

```bash
  git clone https://github.com/jackpots28/IBM-lpar_consistency-check.git
  cd IBM-lpar_consistency-check
  
  #--(Newline list of FQDN HMC's)
  vi hmc.list

  mkdir /tmp/<OUTPUTS>
  chmod 777 /tmp/<OUTPUTS>

  #--(User with ssh passwordless access to HMC's in list)
  cp -r /home/${USER}/.ssh /<PATH>/IBM-lpar_consistency-check

  podman build --build-arg USERNAME=${USER} -t localhost/<IMAGE_NAME>:<TAG> -f docker file
  podman run -v /tmp/<OUTPUTS>:/home/<USERNAME>/IBM-lpar_consistency_output localhost/<IMAGE_NAME>:<TAG>
```
