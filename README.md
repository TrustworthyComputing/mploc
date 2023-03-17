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
make -j8 all
```

## Run
```shell
make setup
echo 1 2 3 4 > Player-Data/Input-P0-0
echo 1 2 3 4 > Player-Data/Input-P1-0
Scripts/compile-run.py -E mascot tutorial
```

