<h1 align="center">MPloC <a href="https://github.com/jimouris/mploc/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg"></a> </h1>

<p align="center">
    <img src="./logos/mploc.jpg" height="90%" width="90%">
</p>

## Overview
TODO: write an overview here ...

Transform Verilog (2005) code into ["Bristol Fashion"](https://homes.esat.kuleuven.be/~nsmart/MPC/) MPC Circuits and run them using [MP-SPDZ](https://github.com/data61/MP-SPDZ).


## Install
### Prerequisites
```shell
sudo apt-get install automake build-essential clang cmake git libboost-dev \
    libboost-thread-dev libntl-dev libsodium-dev libssl-dev libtool m4 python3 \
    texinfo yasm yosys
```

Clone this repository:
```shell
git clone --recurse-submodules git@github.com:jimouris/mploc.git
```

### Build MP-SPDZ
```shell
cd MP-SPDZ
make setup
make Programs/Circuits
make -j8 all
cd ..
```

## Run

### Generate Bristol Circuit
Create the EDIF files with Yosys:
```shell
$ yosys
yosys> read_verilog Programs/Verilog/4_bit_adder.v
yosys> synth
yosys> abc -g XOR,AND
yosys> write_edif Programs/EDIF/4_bit_adder.edif
yosys> exit
```

Convert the edif file to a Bristol fashion circuit:
```shell
python src/edif2bristol.py --edif Programs/EDIF/4_bit_adder.edif --out Programs/Circuits/4_bit_adder.txt
```

### Prepare the Player Data
From the MP-SPDZ directory run:
```shell
mkdir -p Player-Data
echo 4 > Player-Data/Input-P0-0
echo 2 0 > Player-Data/Input-P1-0
```

```shell
./MP-SPDZ/compile.py 4_bit_adder
./MP-SPDZ/Scripts/semi.sh 4_bit_adder
```

<p align="center">
    <img src="./logos/twc.png" height="20%" width="20%">
</p>
<h4 align="center">Trustworthy Computing Group</h4>
