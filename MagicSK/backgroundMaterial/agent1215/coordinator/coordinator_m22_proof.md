# Why the M22 Coefficient Vanishes for Every 4×4 Magic Square

Let `s=(1,-1,-1,1)` and let the unscaled `M22` sign mask be
`S[r,c]=s[r]s[c]`. Let `R_r`, `C_c`, `D`, and `A` be the 0/1 incidence
masks for row `r`, column `c`, the main diagonal, and the anti-diagonal.
Cellwise,

`S = 2D + 2A - (1/2)Σ_r R_r - (1/2)Σ_c C_c`.

The normalized tensor mode is `Ψ22=S/4`, because `φ2=s/2`.

For the centered field `h=a-8.5`, every row, column, and principal diagonal
of a magic square sums to zero. Taking the inner product with the displayed
linear combination therefore gives

`C22 = <h,Ψ22> = 0`.

Thus `M22=0` is an algebraic consequence of all ten magic-line constraints,
not merely an empirical property of the 880-square census. A semimagic
counterexample with incorrect principal diagonal sums does not test this
claim.
