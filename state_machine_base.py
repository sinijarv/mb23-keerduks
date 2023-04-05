
# Empty prototype state class
class State:
    async def on_enter(self) -> None:
        print('wat')
        pass
    
    
    async def on_exit(self) -> None:
        pass
    
    
    async def step(self) -> None:
        pass
    
    
class StateMachine:
    def __init__(self) -> None:
        self.current_state: State = None
        self.prev_state: State = None
        
        
    async def run(self) -> None:
        if self.current_state == self.prev_state:
            await self.current_state.step()
            return

        if self.prev_state is not None:
            await self.prev_state.on_exit()
        await self.current_state.on_enter()
        self.prev_state = self.current_state
        
    def set_state(self, state: State):
        self.current_state = state