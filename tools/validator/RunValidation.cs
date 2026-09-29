using NUnit.Framework;

namespace GuitarHero.Validator;

/// <summary>Ponto de entrada via "dotnet test" (ver o comentário no .csproj).</summary>
[TestFixture]
public class RunValidation
{
    [Test]
    public void ValidarPasta()
    {
        string? folder = Environment.GetEnvironmentVariable("YARG_VALIDAR_PASTA");
        if (string.IsNullOrWhiteSpace(folder))
        {
            Assert.Ignore("defina YARG_VALIDAR_PASTA com a pasta da música ou da biblioteca");
        }
        var (ok, text) = SongValidator.Run(folder!, Environment.GetEnvironmentVariable("YARG_VALIDAR_JSON"));
        TestContext.Out.WriteLine(text);
        Assert.That(ok, Is.True, text);
    }
}
