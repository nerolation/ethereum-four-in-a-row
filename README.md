
# The classical Four in a Row/Connect Four game on Ethereum

The Solidity contract is capable of providing the underlying logic of a Four in a Row game, in which, on a grid with seven columns and 5 rows, two players try to form a horizontal, vertical or diagonal line of four discs to win. 

#### This implementation is highly gas-intensive, however, the whole logic of the game is shifted onto Ethereum. 
#### Only two input variables are required: 
 * ##### an address - in the join function; specifies the virtual-room to join
 * ##### an integer - in the move function; specifies the column chosen by a player for his/her next 
