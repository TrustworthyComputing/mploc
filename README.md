# crispy-broccoli

```shell
git clone --recurse-submodules git@github.com:jimouris/crispy-broccoli.git
```

["Bristol Fashion"](https://homes.esat.kuleuven.be/~nsmart/MPC/) MPC Circuits


## Install
### Prerequisites
```shell
sudo apt-get install automake build-essential clang cmake git libboost-dev \
    libboost-thread-dev libntl-dev libsodium-dev libssl-dev libtool m4 python3 \
    texinfo yasm
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
```shell
yosys
read_verilog verilog/4_bit_adder.v
synth
abc -g XOR,AND
write_edif netlists/4_bit_adder.edif
exit
```
```shell
python src/edif2bristol.py --edif netlists/4_bit_adder.edif --out netlists/4_bit_adder.txt
```

### Prepare the Player Data
From the MP-SPDZ directory run:
```shell
mkdir -p Player-Data
echo 4 > Player-Data/Input-P0-0
echo 2 0 > Player-Data/Input-P1-0
```

```shell
./MP-SPDZ/compile.py adder4
./MP-SPDZ/Scripts/semi.sh adder4
```
